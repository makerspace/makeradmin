from core import service
from service.api_definition import POST, PUBLIC, Arg, symbol, DELETE, GET, SERVICE
from service.db import db_session

TODO = "TODO"


# $app->  post("oauth/token",          "Authentication@login");
@service.route("/oauth/token", method=POST, permission=PUBLIC)
def login(grant_type=Arg(symbol)):
    return "login-" + ",".join(n for i, n in db_session.execute("SELECT user_id, access_token FROM access_tokens"))


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
