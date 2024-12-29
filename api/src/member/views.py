from change_phone_request import change_phone_request, change_phone_validate
from flask import g, request
from membership.member_auth import get_member_permissions
from membership.membership import get_access_summary, get_membership_summary
from membership.models import Member
from membership.views import member_entity
from quiz.views import member_quiz_statistics
from service.api_definition import GET, MESSAGE_SEND, POST, PUBLIC, USER, Arg, natural1, non_empty_str
from service.db import db_session
from service.error import Unauthorized

from member import service
from member.member import (
    get_license_html_text,
    get_member_groups,
    send_access_token_email,
    send_updated_member_info_email,
    set_pin_code,
)


@service.route("/send_access_token", method=POST, permission=PUBLIC)
def send_access_token(redirect=Arg(str, required=False), user_identification: str = Arg(str)):
    """Send access token email to user with username or member_number user_identification."""
    return send_access_token_email(
        redirect or "/member", user_identification, request.remote_addr, request.user_agent.string
    )


@service.route("/send_updated_member_info", method=POST, permission=MESSAGE_SEND)
def send_updated_member_info(member_id: int = Arg(int), msg_swe: str = Arg(str), msg_en: str = Arg(str)):
    """Send email to user with information that personal information has been updated."""
    return send_updated_member_info_email(member_id, msg_swe, msg_en)


@service.route("/current", method=GET, permission=USER)
def current_member():
    """Get current member."""
    m = member_entity.read(g.user_id)

    # Expose if the member has a password set, but not what the password is (not even the hash)
    assert m is not None
    m2 = db_session.query(Member).get(g.user_id)
    assert m2 is not None
    m["has_password"] = m2.password is not None

    return m


@service.route("/current/permissions", method=GET, permission=USER)
def current_permissions():
    """Get current member permissions."""
    return {"permissions": [p for _, p in get_member_permissions(g.user_id)]}


@service.route("/current/membership", method=GET, permission=USER)
def current_membership_info():
    """Get current user membership information."""
    return get_membership_summary(g.user_id).as_json()


@service.route("/current/access", method=GET, permission=USER)
def current_access_info():
    """Get current user accessy information."""
    return get_access_summary(g.user_id)


@service.route("/current/groups", method=GET, permission=USER)
def current_membership_groups():
    return get_member_groups(g.user_id)


@service.route("/current/quizzes", method=GET, permission=USER)
def current_member_quiz_info():
    """Get info about which quizzes the current user has completed."""
    return member_quiz_statistics(g.user_id)


@service.route("/current/set_pin_code", method=POST, permission=USER)
def set_pin_code_endpoint(pin_code=Arg(str)):
    return set_pin_code(g.user_id, pin_code)


@service.route("/send_phone_number_validation_code", method=POST, permission=PUBLIC)
def request_change_phone_number(member_id: int | None = Arg(int, required=False), phone=Arg(non_empty_str)):
    if member_id is not None and member_id != g.user_id:
        raise Unauthorized("You can only change your own phone number.")
    return change_phone_request(member_id, phone)


@service.route("/validate_phone_number", method=POST, permission=PUBLIC)
def validate_change_phone_number(id: int = Arg(int), validation_code=Arg(int)):
    return change_phone_validate(g.user_id, id, validation_code)


@service.route("/licenses", method=GET, permission=USER)
def get_licenses():
    return get_license_html_text()
