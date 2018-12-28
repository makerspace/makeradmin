from flask import request, g

import membership
from core import service
from core.models import Login, AccessToken
from service.api_definition import POST, PUBLIC, Arg, DELETE, GET, SERVICE, Enum, USER
from service.error import ApiError, NotFound

TODO = "TODO"


@service.route("/oauth/token", method=POST, permission=PUBLIC)
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


@service.route("/oauth/token/<string:token>", method=DELETE, permission=USER)
def logout(token=None):
    return AccessToken.remove_token(token, g.user_id)


@service.route("/oauth/resetpassword", method=POST, permission=PUBLIC)
def reset_password():
    raise NotFound("Reset password functionality is not implemented yet.")


# $app->   get("oauth/token",         ["middleware" => "auth", "uses" => "Authentication@listTokens"]);
@service.route("/oauth/token", method=GET, permission=USER)
def list_tokens():
    return AccessToken.list_for_user(g.user_id)


# // Allow other services to get login tokens for any user
# $app->  post("oauth/force_token", ["middleware" => "auth:service", "uses" => "Authentication@unauthenticated_login"]);
@service.route("/oauth/force_token", method=POST, permission=SERVICE)
def force_token():
    return ""
