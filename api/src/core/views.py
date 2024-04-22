from flask import g, request
from service.api_definition import DELETE, GET, PERMISSION_MANAGE, POST, PUBLIC, USER, Arg, Enum, non_empty_str
from service.error import BadRequest

from core import auth, service


@service.route("/oauth/token", method=POST, permission=PUBLIC, flat_return=True)
def login(grant_type=Arg(Enum("password")), username=Arg(str), password=Arg(str)):
    """Login user with username/email/member number and password, returns token."""
    assert grant_type
    username = username.strip().lower()
    password = password.strip()
    return auth.login(request.remote_addr, request.user_agent.string, username, password)


@service.route("/oauth/token/<string:token>", method=DELETE, permission=USER)
def logout(token=None):
    """Remove token from database, returns None."""
    return auth.remove_token(token, g.user_id)


@service.route("/oauth/request_password_reset", method=POST, permission=PUBLIC)
def request_password_reset(user_identification: str = Arg(non_empty_str), redirect: str = Arg(non_empty_str)):
    """Send a reset password link to the users email."""
    user_identification = user_identification.strip()
    redirect = redirect.strip()
    return auth.request_password_reset(user_identification, redirect)


@service.route("/oauth/password_reset", method=POST, permission=PUBLIC)
def password_reset(reset_token: str = Arg(non_empty_str), unhashed_password: str = Arg(str)):
    """Reset the password for a user."""
    return auth.password_reset(reset_token, unhashed_password)


@service.route("/oauth/token", method=GET, permission=USER)
def list_tokens():
    """List all tokens for the authorized user."""
    return auth.list_for_user(g.user_id)


@service.route("/oauth/service_token", method=GET, permission=PERMISSION_MANAGE)
def list_service_tokens():
    """List all service tokens."""
    return auth.list_service_tokens()


@service.route("/oauth/service_token/<user_id>", method=DELETE, permission=PERMISSION_MANAGE, status="deleted")
def roll_service_token(user_id=None):
    """Roll service token in the database, returns None."""
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise BadRequest(f"Can not convert arg to int.")

    if user_id >= 0:
        raise BadRequest(f"Can only roll tokens for service users.")

    return auth.roll_service_token(user_id)
