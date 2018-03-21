from flask import abort, jsonify
import pymysql
import sys
import os
import requests
import socket
import signal


class DB:
    def __init__(self, host, name, user, password):
        self.host = host
        self.name = name
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = pymysql.connect(host=self.host.split(":")[0], port=int(self.host.split(":")[1]), db=self.name, user=self.user, password=self.password)

    def cursor(self):
        return self.connection.cursor()


class APIGateway:
    def __init__(self, host, key):
        self.host = host
        self.key = key

    def get(self, path, payload=None):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.get('http://' + self.host + "/" + path, params=payload, headers=headers)

    def post(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.post('http://' + self.host + "/" + path, json=payload, headers=headers)

    def put(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.put('http://' + self.host + "/" + path, json=payload, headers=headers)


class Service:
    def __init__(self, name, url, port, version, db, gateway, debug):
        self.name = name
        self.url = url
        self.port = port
        self.version = version
        self.db = db
        self.debug = debug
        self.gateway = gateway

    def full_path(self, path):
        return "/" + self.url + "/" + path

    def register(self):
        payload = {
            "name": self.name,
            "url": self.url,
            "endpoint": "http://" + socket.gethostname() + ":" + str(self.port) + "/",
            "version": self.version
        }
        r = self.gateway.post("service/register", payload)
        if not r.ok:
            raise Exception("Failed to register service: " + r.text)

    def unregister(self):
        payload = {
            "url": self.url,
            "version": self.version
        }
        r = self.gateway.post("service/unregister", payload)
        if not r.ok:
            raise Exception("Failed to unregister service: " + r.text)

    def wrap_error_codes(self, app):
        # Pretty ugly way to wrap all abort(code, message) calls so that they return proper json reponses
        def create_wrapper(status_code):
            @app.errorhandler(status_code)
            def custom_error(error):
                response = jsonify({'status': error.description})
                response.status_code = status_code
                return response
        for i in range(400, 500):
            try:
                create_wrapper(i)
            except:
                pass

    def serve_indefinitely(self, app):
        capture_signals()
        self.wrap_error_codes(app)
        app.run(host='0.0.0.0', debug=self.debug, port=self.port, use_reloader=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        eprint("Closing database connection")
        self.db.connection.close()
        self.unregister()


def assert_get(data, key):
    if key not in data:
        abort(400, "Missing required parameter " + key)

    return data[key]


def _read_config():
    try:
        db = DB(
            host=os.environ["MYSQL_HOST"],
            name=os.environ["MYSQL_DB"],
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASS"],
        )

        gateway = APIGateway(os.environ["APIGATEWAY"], os.environ["BEARER"])

        debugStr = os.environ["APP_DEBUG"].lower()
        if debugStr == "true" or debugStr == "false":
            debug = debugStr == "true"
        else:
            raise Exception("APP_DEBUG environment variable must be either 'true' or 'false'. Found '{}'".format(debugStr))
    except Exception as e:
        eprint("Missing one or more configuration environment variables")
        sys.exit(1)
    return db, gateway, debug


def eprint(s, **kwargs):
    ''' Print to stderr and flush the output stream '''
    print(s, **kwargs, file=sys.stderr)
    sys.stderr.flush()


def capture_signals():
    def signal_handler(signal, frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)


def create(name, url, port, version):
    db, gateway, debug = _read_config()
    service = Service(name, url, port, version, db, gateway, debug)

    service.unregister()
    eprint("Registering service...")
    service.register()

    eprint("Connecting to database...")
    db.connect()
    return service
