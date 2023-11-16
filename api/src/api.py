import flask_cors
from flask import Flask, jsonify
from flask.wrappers import Response as FlaskResponse
from sqlalchemy.exc import OperationalError
from core.auth import authenticate_request
from membership.permissions import register_permissions
from service.api_definition import ALL_PERMISSIONS
from service.config import get_mysql_config, config
from service.db import create_mysql_engine, shutdown_session, populate_fields_by_index
from service.error import (
    ApiError,
    error_handler_api,
    error_handler_db,
    error_handler_500,
    error_handler_404,
    error_handler_400,
    error_handler_405,
)
from service.traffic_logger import traffic_logger_init, traffic_logger_commit
from services import services
from shop.stripe_setup import setup_stripe

app = Flask(__name__, static_folder=None)


flask_cors.CORS(
    app,
    max_age="1728000",
    allow_headers=[
        "Origin",
        "Content-Type",
        "Accept",
        "Authorization",
        "X-Request-With",
        "Access-Control-Allow-Origin",
    ],
    origins=config.get("CORS_ALLOWED_ORIGINS").split(","),
)


for path, service in services:
    app.register_blueprint(service, url_prefix=path)


def before_request_functions():
    traffic_logger_init()
    authenticate_request()


def after_request_functions(response: FlaskResponse):
    response.direct_passthrough = False
    traffic_logger_commit(response)
    return response


app.register_error_handler(OperationalError, error_handler_db)
app.register_error_handler(ApiError, error_handler_api)
app.register_error_handler(400, error_handler_400)
app.register_error_handler(404, error_handler_404)
app.register_error_handler(405, error_handler_405)
app.register_error_handler(500, error_handler_500)
app.teardown_appcontext(shutdown_session)
app.before_request(before_request_functions)
app.after_request(after_request_functions)


engine = create_mysql_engine(**get_mysql_config())


populate_fields_by_index(engine)
register_permissions(ALL_PERMISSIONS)

setup_stripe()


@app.route("/")
def index():
    return jsonify(dict(status="ok")), 200


@app.route("/routes")
def routes():
    return "\n".join(sorted([f"{rule.rule}: {', '.join(sorted(rule.methods))}" for rule in app.url_map.iter_rules()]))
