from flask import Flask
from sqlalchemy.exc import OperationalError

from core.models import AccessToken
from service.config import get_mysql_config
from service.db import create_mysql_engine, shutdown_session
from service.error import ApiError, api_error_handler, db_error_handler
from services import services

app = Flask(__name__)

for path, service in services:
    app.register_blueprint(service, path=path)

app.register_error_handler(OperationalError, db_error_handler)
app.register_error_handler(ApiError, api_error_handler)
app.teardown_appcontext(shutdown_session)
app.before_request(AccessToken.authenticate_request)

engine = create_mysql_engine(**get_mysql_config())


# TODO Use Sentry?

@app.route("/")
def index():
    return "/"
    # // Index page, test to see if the user is logged in or not
    # $app->  get("/", ["middleware" => "auth:service", "uses" => "ServiceRegistry@test"]);


# TODO Make sure nobody calls this and remove it.
@app.route("/service/register")
def service_register():
    return "ok", 200


# TODO Make sure nobody calls this and remove it.
@app.route("/service/unregister")
def service_unregister():
    return "ok", 200

    
# // OAuth 2.0 stuff
# $app->  post("oauth/token",          "Authentication@login");
# $app->  post("oauth/resetpassword",  "Authentication@reset");
# $app->   get("oauth/token",         ["middleware" => "auth", "uses" => "Authentication@listTokens"]);
# $app->delete("oauth/token/{token}", ["middleware" => "auth", "uses" => "Authentication@logout"]);
#
# // Allow other services to get login tokens for any user
# $app->  post("oauth/force_token", ["middleware" => "auth:service", "uses" => "Authentication@unauthenticated_login"]);
#
# // Service registry
# $app->post("service/register",   ["middleware" => "auth:service", "uses" => "ServiceRegistry@register"]);
# $app->post("service/unregister", ["middleware" => "auth:service", "uses" => "ServiceRegistry@unregister"]);
