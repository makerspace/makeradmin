from core import service
from service import logger
from service.db import db_session

POST = 'POST'
GET = 'GET'


PUBLIC = 'public'
SERVICE = 'service'


@service.route("/oauth/token") #, method=POST, permission=PUBLIC)
def login():
    return "login-" + ",".join(n for i, n in db_session.execute("SELECT id, name FROM migrations"))


# @service.route("oath/token", method=GET, permission=SERVICE)
# def list_tokens():
#     return "list_tokens"


# // OAuth 2.0 stuff
# $app->  post("oauth/token",          "Authentication@login");
# $app->  post("oauth/resetpassword",  "Authentication@reset");
# $app->   get("oauth/token",         ["middleware" => "auth", "uses" => "Authentication@listTokens"]);
# $app->delete("oauth/token/{token}", ["middleware" => "auth", "uses" => "Authentication@logout"]);
