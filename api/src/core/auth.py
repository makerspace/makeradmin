import secrets
from datetime import datetime, timedelta, timezone
from logging import getLogger
from string import ascii_letters, digits
from typing import Optional
from urllib.parse import quote_plus

from flask import g, jsonify, request
from membership.member_auth import authenticate, check_and_hash_password, get_member_permissions
from membership.models import Member
from messages.message import send_message
from messages.models import MessageTemplate
from service import config
from service.api_definition import BAD_VALUE, EXPIRED, REQUIRED, USER
from service.db import db_session
from service.error import (
    ApiError,
    BadRequest,
    InternalServerError,
    NotFound,
    TooManyRequests,
    Unauthorized,
    UnprocessableEntity,
)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from core.models import AccessToken, Login, PasswordResetToken
from core.service_users import SERVICE_NAMES, SERVICE_PERMISSIONS

logger = getLogger("makeradmin")


def generate_token() -> str:
    return "".join(secrets.choice(ascii_letters + digits) for _ in range(32))


def get_member_by_user_identification(user_identification):
    try:
        if user_identification.isdigit():
            return db_session.query(Member).filter_by(member_number=int(user_identification), deleted_at=None).one()

        return db_session.query(Member).filter_by(email=user_identification, deleted_at=None).one()

    except NoResultFound:
        raise NotFound(
            f"Could not find any user with the name or email '{user_identification}'.",
            fields="user_identification",
            status="not found",
        )


def create_access_token(ip: str, browser: Optional[str], user_id: int, valid_duration: Optional[timedelta] = None):
    assert user_id > 0

    access_token = AccessToken(
        user_id=user_id,
        access_token=generate_token(),
        browser=browser,
        ip=ip,
        expires=datetime.now(timezone.utc) + (timedelta(minutes=15) if valid_duration is None else valid_duration),
        lifetime=int(timedelta(days=14).total_seconds()),
    )

    db_session.add(access_token)

    return dict(access_token=access_token.access_token, expires=access_token.expires.isoformat())


def login(ip, browser, username, password):
    count = Login.get_failed_login_count(ip)

    if count > 10:
        raise TooManyRequests(
            "Your have reached your maximum number of failed login attempts for the last hour."
            " Please try again later."
        )

    try:
        member_id = authenticate(username=username, password=password)
    except ApiError:
        Login.register_login_failed(ip)
        raise

    Login.register_login_success(ip, member_id)

    return create_access_token(ip, browser, member_id)


def request_password_reset(user_identification: str, redirect: str):
    member = get_member_by_user_identification(user_identification)

    token = generate_token()

    db_session.add(PasswordResetToken(member_id=member.member_id, token=token))
    db_session.flush()

    if redirect == "admin":
        url = config.get_admin_url("/password-reset")
    elif redirect == "member":
        url = config.get_public_url("/member/reset_password")
    else:
        raise BadRequest("Invalid redirect", fields="redirect", what=BAD_VALUE)
    url += f"?reset_token={quote_plus(token)}"

    if config.debug_mode():
        logger.info(f"Reset link for {member.email} is {url}")

    send_message(
        MessageTemplate.PASSWORD_RESET,
        member,
        url=url,
    )


def password_reset(reset_token, unhashed_password):
    try:
        password_reset_token = db_session.query(PasswordResetToken).filter_by(token=reset_token).one()

    except NoResultFound:
        raise UnprocessableEntity("Could not find password reset token, try to request a new reset link.")

    except MultipleResultsFound:
        raise InternalServerError(log=f"Multiple tokens {reset_token} found, this is a bug.")

    if datetime.now(timezone.utc) - password_reset_token.created_at > timedelta(minutes=10):
        raise UnprocessableEntity("Reset link expired, try to request a new one.")

    try:
        hashed_password = check_and_hash_password(unhashed_password)
    except ValueError as e:
        raise BadRequest(str(e))

    try:
        member = db_session.query(Member).get(password_reset_token.member_id)
    except NoResultFound:
        raise InternalServerError(log=f"No member with id {password_reset_token.member_id} found, this is a bug.")

    member.password = hashed_password
    db_session.add(member)

    # Prevent the reset tokens from being reused
    db_session.query(PasswordResetToken).filter(PasswordResetToken.id == password_reset_token.id).delete()
    db_session.flush()
    print("Password reset for", member.email)

    return {}


def force_login(ip: str, browser: str, user_id: int):
    Login.register_login_success(ip, user_id)
    return create_access_token(ip, browser, user_id)


def remove_token(token, user_id):
    assert user_id > 0

    count = (
        db_session.query(AccessToken).filter(AccessToken.user_id == user_id, AccessToken.access_token == token).delete()
    )

    if not count:
        raise NotFound("The access_token you specified could not be found in the database.")

    return None


def list_for_user(user_id):
    return [
        dict(
            access_token=access_token.access_token,
            browser=access_token.browser,
            ip=access_token.ip,
            expires=access_token.expires.isoformat(),
        )
        for access_token in db_session.query(AccessToken).filter(AccessToken.user_id == user_id)
    ]


def roll_service_token(user_id):
    try:
        access_token = db_session.query(AccessToken).filter_by(user_id=user_id).one()
        access_token.access_token = generate_token()
        db_session.add(access_token)
    except NoResultFound:
        raise NotFound()

    except MultipleResultsFound as e:
        raise Exception(f"Found multiple of service token id {user_id}, this is a bug.") from e


def list_service_tokens():
    return [
        dict(
            user_id=access_token.user_id,
            service_name=SERVICE_NAMES.get(access_token.user_id, "unknown service"),
            access_token=access_token.access_token,
            permissions=",".join(SERVICE_PERMISSIONS.get(access_token.user_id, [])),
        )
        for access_token in db_session.query(AccessToken).filter(AccessToken.user_id < 0)
    ]
