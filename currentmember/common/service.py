from flask import abort, jsonify, request
from werkzeug.exceptions import NotFound
import pymysql
import sys
import os
import requests
import socket
import signal
from functools import wraps

SERVICE_USER_ID = -1


class DB:
    def __init__(self, host, name, user, password):
        self.host = host
        self.name = name
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        # Note autocommit is required to make updates from other services visible immediately
        self.connection = pymysql.connect(host=self.host.split(":")[0], port=int(self.host.split(":")[1]), db=self.name, user=self.user, password=self.password, autocommit=True)

    def cursor(self):
        return self.connection.cursor()


class APIGateway:
    def __init__(self, host, key, host_frontend, host_backend):
        self.host = host
        self.host_frontend = host_frontend
        self.host_backend = host_backend
        self.auth_headers = {"Authorization": "Bearer " + key}

    def get_frontend_url(self, path):
        return "http://" + self.host_frontend + "/" + path

    def get(self, path, payload=None):
        return requests.get('http://' + self.host + "/" + path, params=payload, headers=self.auth_headers)

    def post(self, path, payload):
        return requests.post('http://' + self.host + "/" + path, json=payload, headers=self.auth_headers)

    def put(self, path, payload):
        return requests.put('http://' + self.host + "/" + path, json=payload, headers=self.auth_headers)


class Service:
    def __init__(self, name, url, port, version, db, gateway, debug, frontend):
        self.name = name
        self.url = url
        self.port = port
        self.version = version
        self.db = db
        self.debug = debug
        self.gateway = gateway
        self.frontend = frontend

    def full_path(self, path):
        return "/" + self.url + "/" + path

    def register(self):
        # Frontend services do not register themselves as API endpoints
        if not self.frontend:
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
        if not self.frontend:
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


def read_config():
    try:
        db = DB(
            host=os.environ["MYSQL_HOST"],
            name=os.environ["MYSQL_DB"],
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASS"],
        )

        gateway = APIGateway(os.environ["APIGATEWAY"], os.environ["BEARER"], os.environ["HOST_FRONTEND"], os.environ["HOST_BACKEND"])

        debugStr = os.environ["APP_DEBUG"].lower()
        if debugStr == "true" or debugStr == "false":
            debug = debugStr == "true"
        else:
            raise Exception("APP_DEBUG environment variable must be either 'true' or 'false'. Found '{}'".format(debugStr))
    except Exception as e:
        eprint("Missing one or more configuration environment variables")
        eprint(e)
        sys.exit(1)
    return db, gateway, debug


def eprint(s, **kwargs):
    ''' Print to stderr and flush the output stream '''
    print(s, **kwargs, file=sys.stderr)
    sys.stderr.flush()


def capture_signals():
    def signal_handler(signal, frame):
        raise KeyboardInterrupt()

    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
        signal.signal(sig, signal_handler)


def create(name, url, port, version):
    db, gateway, debug = read_config()
    service = Service(name, url, port, version, db, gateway, debug, False)
    service.unregister()
    eprint("Registering service...")
    service.register()

    eprint("Connecting to database...")
    db.connect()
    return service


def create_frontend(url, port):
    db, gateway, debug = read_config()
    service = Service(None, url, port, None, db, gateway, debug, True)
    eprint("Connecting to database...")
    db.connect()
    return service


def route_helper(f, json=False):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if json:
            data = request.get_json()
            if data is None:
                abort(400, "missing json")

        try:
            res = f(data, *args, **kwargs) if json else f(*args, **kwargs)
        except NotFound:
            return jsonify({"status": "not found"}), 404

        if res is not None:
            return jsonify({
                "status": "ok",
                "data": res
            })
        return jsonify({"status": "ok"})
    return wrapper


class Entity:
    def __init__(self, table, columns, read_transforms={}, write_transforms={}):
        self.table = table
        self.columns = columns
        self.all_columns = self.columns[:]
        self.all_columns.insert(0, "id")
        self.read_transforms = read_transforms
        self.write_transforms = write_transforms
        self.db = None

        for c in self.all_columns:
            if c not in read_transforms:
                read_transforms[c] = lambda x: x
            if c not in write_transforms:
                write_transforms[c] = lambda x: x

        self.fields = ",".join(self.columns)
        self.all_fields = ",".join(self.all_columns)

    def get(self, id):
        with self.db.cursor() as cur:
            cur.execute("SELECT {} FROM {} WHERE id=%s".format(self.all_fields, self.table), (id,))
            item = cur.fetchone()
            if item is None:
                raise NotFound()

            return {
                self.all_columns[i]: self.read_transforms[self.all_columns[i]](item[i]) for i in range(len(self.all_columns))
            }

    def put(self, data, id):
        with self.db.cursor() as cur:
            values = [self.write_transforms[col](data[col]) for col in self.columns]
            cur.execute("UPDATE {} SET {} WHERE id=%s".format(self.table, ",".join(col + "=%s" for col in self.columns)), (*values, id))

    def post(self, data):
        with self.db.cursor() as cur:
            values = [self.write_transforms[col](data[col]) for col in self.columns]
            cur.execute("INSERT INTO {} ({}) VALUES({})".format(self.table, self.fields, ",".join(["%s"] * len(self.columns))), values)

            return {"id": cur.lastrowid}

    def delete(self, id):
         with self.db.cursor() as cur:
            cur.execute("UPDATE {} SET deleted_at=CURRENT_TIMESTAMP WHERE id=%s".format(self.table), (id,))

    def list(self, where="deleted_at IS NULL", where_values=[]):
        with self.db.cursor() as cur:
            cur.execute("SELECT {} FROM {} {}".format(self.all_fields, self.table, "WHERE " + where if where is not None else ""), where_values)
            rows = cur.fetchall()
            return [{
                self.all_columns[i]: self.read_transforms[self.all_columns[i]](item[i]) for i in range(len(self.all_columns))
            } for item in rows]

    def add_routes(self, app, endpoint):
        # Note: Many methods here return other methods that we then call.
        # The endpoint keyword argument is just because flask needs something unique, it doesn't matter what it is for our purposes
        app.route(endpoint + "/<int:id>", endpoint=endpoint+".get", methods=["GET"])(route_helper(self.get))
        app.route(endpoint + "/<int:id>", endpoint=endpoint+".put", methods=["PUT"])(route_helper(self.put, json=True))
        app.route(endpoint + "/<int:id>", endpoint=endpoint+".delete", methods=["DELETE"])(route_helper(self.delete))
        app.route(endpoint + "", endpoint=endpoint+".post", methods=["POST"])(route_helper(self.post, json=True))
        app.route(endpoint + "", endpoint=endpoint+".list", methods=["GET"])(route_helper(self.list))
