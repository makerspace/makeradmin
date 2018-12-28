from flask import request

import membership
from core import service
from core.models import Login, AccessToken
from service.api_definition import POST, PUBLIC, Arg, DELETE, GET, SERVICE, Enum
from service.error import ApiError

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

    # TODO We need to commit here, or do we do auto commit?

    return AccessToken.create_user_token(member_id)


# $app->delete("oauth/token/{token}", ["middleware" => "auth", "uses" => "Authentication@logout"]);
@service.route("/oauth/token/<string:token>", method=DELETE, permission=TODO)
def logout(token=None):
    return ""


# $app->  post("oauth/resetpassword",  "Authentication@reset");
@service.route("/oauth/resetpassword", method=POST, permission=PUBLIC)
def reset_password():
    return ""


# $app->   get("oauth/token",         ["middleware" => "auth", "uses" => "Authentication@listTokens"]);
@service.route("/oauth/token", method=GET, permission=TODO)
def list_tokens():
    return "list_tokens"


# // Allow other services to get login tokens for any user
# $app->  post("oauth/force_token", ["middleware" => "auth:service", "uses" => "Authentication@unauthenticated_login"]);
@service.route("/oauth/force_token", method=POST, permission=SERVICE)
def force_token():
    return ""
