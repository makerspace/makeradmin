import flask_cors
from flask import Flask, jsonify
from sqlalchemy.exc import OperationalError

from core.models import AccessToken
from service.config import get_mysql_config
from service.db import create_mysql_engine, shutdown_session
from service.error import ApiError, error_handler_api, error_handler_db, error_handler_500, error_handler_404
from services import services

app = Flask(__name__)

flask_cors.CORS(
    app,
    max_age='1728000',
    allow_headers=['Origin', 'Content-Type', 'Accept', 'Authorization', 'X-Request-With',
                   'Access-Control-Allow-Origin'],
)

for path, service in services:
    app.register_blueprint(service, url_prefix=path)


app.register_error_handler(OperationalError, error_handler_db)
app.register_error_handler(ApiError, error_handler_api)
app.register_error_handler(500, error_handler_500)
app.register_error_handler(404, error_handler_404)
app.teardown_appcontext(shutdown_session)
app.before_request(AccessToken.authenticate_request)

engine = create_mysql_engine(**get_mysql_config())


@app.route("/")
def index():
    return jsonify(dict(status="ok")), 200


# TODO Use Sentry?
