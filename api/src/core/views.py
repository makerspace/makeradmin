from flask import request, g

import membership
from core import service
from core.models import Login, AccessToken
from service.api_definition import POST, PUBLIC, Arg, DELETE, GET, SERVICE, Enum, USER, BAD_VALUE
from service.error import ApiError, NotFound, UnprocessableEntity


@service.route("/oauth/token", method=POST, permission=PUBLIC, flat_return=True)
def login(grant_type=Arg(Enum('password')), username=Arg(str), password=Arg(str)):
    assert grant_type

    Login.check_should_throttle(request.remote_addr)

    try:
        data = membership.service.service_post('/authenticate', username=username, password=password)
        member_id = data.get('member_id')
    except ApiError:
        Login.register_login_failed(request.remote_addr)
        raise
    
    Login.register_login_success(request.remote_addr, member_id)
    
    return AccessToken.create_user_token(member_id)


# TODO Can maybe be solved by generic entity stuff?
@service.route("/oauth/token/<string:token>", method=DELETE, permission=USER)
def logout(token=None):
    return AccessToken.remove_token(token, g.user_id)


@service.route("/oauth/resetpassword", method=POST, permission=PUBLIC)
def reset_password():
    raise NotFound("Reset password functionality is not implemented yet.")


# TODO Can maybe be solved by generic entity stuff?
@service.route("/oauth/token", method=GET, permission=USER)
def list_tokens():
    return AccessToken.list_for_user(g.user_id)


@service.route("/oauth/force_token", method=POST, permission=SERVICE, flat_return=True)
def force_token(user_id: int=Arg(int)):
    """ Create token for any user. """
    if user_id <= 0:
        raise UnprocessableEntity(fields='user_id', what=BAD_VALUE)
    
    Login.register_login_success(request.remote_addr, user_id)
    
    return AccessToken.create_user_token(user_id)
