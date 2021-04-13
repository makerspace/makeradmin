from flask import request, g

from core import service, auth
from service.api_definition import POST, PUBLIC, Arg, DELETE, GET, Enum, USER, non_empty_str, PERMISSION_MANAGE
from service.error import BadRequest


@service.route("/oauth/token", method=POST, permission=PUBLIC, flat_return=True)
def login(grant_type=Arg(Enum('password')), username=Arg(str), password=Arg(str)):
    """ Login user with username and password, returns token. """
    assert grant_type

    return auth.login(request.remote_addr, request.user_agent.string, username, password)


@service.route("/oauth/token/<string:token>", method=DELETE, permission=USER)
def logout(token=None):
    """ Remove token from database, returns None. """
    return auth.remove_token(token, g.user_id)


@service.route("/oauth/request_password_reset", method=POST, permission=PUBLIC)
def request_password_reset(user_identification: str=Arg(non_empty_str)):
    """ Send a reset password link to the users email. """
    return auth.request_password_reset(user_identification)


@service.route("/oauth/password_reset", method=POST, permission=PUBLIC)
def password_reset(reset_token: str=Arg(non_empty_str), unhashed_password: str=Arg(str)):
    """ Reset the password for a user. """
    return auth.password_reset(reset_token, unhashed_password)


@service.route("/oauth/token", method=GET, permission=USER)
def list_tokens():
    """ List all tokens for the authorized user. """
    return auth.list_for_user(g.user_id)


@service.route("/oauth/service_token", method=GET, permission=PERMISSION_MANAGE)
def list_service_tokens():
    """ List all service tokens. """
    return auth.list_service_tokens()


@service.route("/oauth/service_token/<user_id>", method=DELETE, permission=PERMISSION_MANAGE, status='deleted')
def roll_service_token(user_id=None):
    """ Roll service token in the database, returns None. """
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise BadRequest(f"Can not convert arg to int.")
    
    if user_id >= 0:
        raise BadRequest(f"Can only roll tokens for service users.")
        
    return auth.roll_service_token(user_id)
