import flask_cors
from flask import Flask, Response, request
from sqlalchemy.exc import OperationalError

from core.models import AccessToken
from service.config import get_mysql_config
from service.db import create_mysql_engine, shutdown_session
from service.error import ApiError, api_error_handler, db_error_handler
from service.logging import logger
from services import services

app = Flask(__name__)

flask_cors.CORS(
    app,
    allow_headers=['Origin', 'Content-Type', 'Accept', 'Authorization', 'X-Request-With',
                   'Access-Control-Allow-Origin'],
    max_age='1728000',
)

for path, service in services:
    app.register_blueprint(service, url_prefix=path)


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


