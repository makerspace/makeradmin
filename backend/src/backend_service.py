from logging import getLogger, basicConfig, INFO, WARNING

from flask import jsonify, request, Blueprint, current_app, make_response
from werkzeug.exceptions import NotFound, MethodNotAllowed
import pymysql
import sys
import os
import requests
import socket
import signal
from time import sleep
from functools import wraps
from dataclasses import dataclass
from typing import Callable, Type, Optional, Set, Dict, Union
from datetime import datetime
from dateutil import parser
from decimal import Decimal
from flask import abort as flask_abort

SERVICE_USER_ID = -1


basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)
getLogger('stripe').setLevel(WARNING)


logger = getLogger('makeradmin')


def abort(code, tag):
    flask_abort(make_response(jsonify(status=tag), code))


class BackendException(Exception):
    def __init__(self, sv=None, en=None, tag=None):
        self.tag = tag or self.__class__.__name__
        self.message_sv = sv
        self.message_en = en

    def __str__(self):
        return f'{self.tag}("{self.message_en or self.message_sv}")'


class MissingFieldException(BackendException):
    def __init__(self, field):
        super().__init__(sv=f"Fältet {field} fattas.",
                         en=f"Missing the field {field}.")


class DB:
    def __init__(self, host: str, name: str, user: str, password: str) -> None:
        self.host = host
        self.name = name
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        # Note autocommit is required to make updates from other services visible immediately
        logger.info(f"connecting to database {self.host}")
        self.connection = pymysql.connect(host=self.host.split(":")[0], port=int(self.host.split(":")[1]), db=self.name, user=self.user, password=self.password, autocommit=True)

    def cursor(self):
        self.connection.ping(reconnect=True)
        return self.connection.cursor()


class APIGateway:
    def __init__(self, host: str, key: str, host_backend: str, host_public: str) -> None:
        self.host = self._ensure_protocol(host)
        self.host_public = self._ensure_protocol(host_public)
        self.auth_headers = {"Authorization": "Bearer " + key}

    def _get_headers(self, token):
        return self.auth_headers if token is None else {"Authorization": "Bearer " + token}

    @staticmethod
    def _ensure_protocol(host: str) -> str:
        if not host.startswith("http://") and not host.startswith("https://"):
            host = "http://" + host
        return host

    def get_public_url(self, path):
        host = self.host_public
        return f"{host}{path}"

    def get(self, path, payload=None, token=None) -> requests.Response:
        url = self.host + "/" + path
        headers = self._get_headers(token)
        # logger.info(f"getting url={url}, headers={headers}, params={payload}")  # TODO Remove
        return requests.get(url, params=payload, headers=headers)

    def post(self, path, payload, token=None) -> requests.Response:
        return requests.post(self.host + "/" + path, json=payload, headers=self._get_headers(token))

    def put(self, path, payload, token=None) -> requests.Response:
        return requests.put(self.host + "/" + path, json=payload, headers=self._get_headers(token))

    def delete(self, path, token=None) -> requests.Response:
        return requests.delete(self.host + "/" + path, headers=self._get_headers(token))


DEFAULT_PERMISSION = "service"


def format_datetime(date: Union[str, datetime]):
    if date is None:
        return None

    if not isinstance(date, datetime):
        date = parser.parse(date)

    return date.strftime("%Y-%m-%d %H:%M")


class Service:
    def __init__(self, name: str, url: str, port: int, version: Optional[str], db: DB, gateway: APIGateway, debug: bool) -> None:
        self.name = name
        self.url = url
        self.port = port
        self.version = version
        self.db = db
        self.debug = debug
        self.gateway = gateway
        self._used_permissions: Set[str] = set()
        self.blueprint = Blueprint(name, __name__)
        self.blueprint.context_processor(lambda: dict(url=self.full_path))

    def full_path(self, path: str):
        return "/" + self.url + ("/" + path if path != "" else "")

    def route(self, path: str, permission=DEFAULT_PERMISSION, **kwargs):
        if permission and permission not in (DEFAULT_PERMISSION, 'user'):
            self._used_permissions.add(permission)

        path = self.full_path(path)

        def wrapper(f):
            @wraps(f)
            def auth(*args, **kwargs):
                if permission is not None:
                    permissions = request.headers.get("X-User-Permissions", "").split(",")
                    if permission not in permissions and "service" not in permissions:
                        abort(403, "user does not have the " + str(permission) + " permission")

                return f(*args, **kwargs)
            
            return self.blueprint.route(path, **kwargs)(auth)
        return wrapper

    def register(self):
        endpoint = "http://" + socket.gethostname() + ":" + str(self.port) + "/"
        # logger.info(f"registering service {self.name}, url: {self.url}, endpoint: {endpoint}")
        payload = {
            "name": self.name,
            "url": self.url,
            "endpoint": endpoint,
            "version": self.version
        }
        r = self.gateway.post("service/register", payload)
        if not r.ok:
            pass
            # logger.warning(f"failed to register service {self.name} at {self.gateway.host}, ignoring: {r.json().get('message')}")

    def unregister(self):
        # logger.info(f"unregistering service {self.name}, url: {self.url}")
        payload = {
            "url": self.url,
            "version": self.version
        }
        r = self.gateway.post("service/unregister", payload)
        if not r.ok:
            raise Exception(f"Failed to unregister service at {self.gateway.host}: {r.text}")

    def _wrap_error_codes(self):
        # Pretty ugly way to wrap all abort(code, message) calls so that they return proper json reponses
        def create_wrapper(status_code):
            @self.app.errorhandler(status_code)
            def custom_error(error):
                response = jsonify({'status': error.description})
                response.status_code = status_code
                return response
        for i in range(400, 500):
            try:
                create_wrapper(i)
            except:
                pass

    def add_route_list(self):
        '''Adds an endpoint (/routes) for listing all routes of the service'''
        @self.route("routes", permission=None)
        def site_map():
            return jsonify({"data": [{"url": rule.rule, "methods": list(rule.methods)} for rule in current_app.url_map.iter_rules()]})

    def _register_permissions(self):
        permissions = ",".join(self._used_permissions)
        logger.info(f"{self.name} registering permissions ({permissions})")
        self.gateway.post("membership/permission/register", {
            "service": self.name,
            "permissions": permissions,
        })

    def serve_indefinitely(self):
        self.add_route_list()
        self._wrap_error_codes()
        self._register_permissions()

        def signal_handler(signal, frame):
            eprint("Closing database connection")
            self.db.connection.close()
            self.unregister()
            exit(0)

        for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
            signal.signal(sig, signal_handler)


def assert_get(data: Dict, key: str):
    if key not in data:
        abort(400, "Missing required parameter " + key)

    return data[key]


def gateway_from_envfile(path):
    # Read the .env file
    with open(".env") as f:
        env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}
    host = env["HOST_BACKEND"]
    return APIGateway(host, env["API_BEARER"], env["HOST_BACKEND"], env["HOST_PUBLIC"])


def read_config():
    try:
        db = DB(
            host=os.environ["MYSQL_HOST"],
            name=os.environ["MYSQL_DB"],
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASS"],
        )

        gateway = APIGateway(os.environ["APIGATEWAY"], os.environ["BEARER"], os.environ["HOST_BACKEND"], os.environ["HOST_PUBLIC"])

        debugStr = os.environ["APP_DEBUG"].lower()
        if debugStr == "true" or debugStr == "false":
            debug = debugStr == "true"
        else:
            raise Exception(f"APP_DEBUG environment variable must be either 'true' or 'false'. Found '{debugStr}'")
    except Exception as e:
        eprint("Missing one or more configuration environment variables")
        eprint(e)
        sys.exit(1)
    return db, gateway, debug


def eprint(s, **kwargs):
    ''' Print to stderr and flush the output stream '''
    kwargs.setdefault("file", sys.stderr)
    print(s, **kwargs)
    sys.stderr.flush()


def create(name, url, port, version):
    db, gateway, debug = read_config()
    service = Service(name, url, port, version, db, gateway, debug)

    try:
        service.unregister()
    except:
        # Python sometimes starts so quickly that the API-Gateway module has not managed to initialize itself yet
        # So the initial unregister call may fail. If it does, wait for a few seconds and then try again.
        sleep(2)
        service.unregister()

    service.register()

    db.connect()
    return service


def route_helper(f, json=False, status="ok"):
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
        except BackendException as e:
            logger.info(f"returning 400 to user: {str(e)}")
            return jsonify({"status": e.tag, "message_sv": e.message_sv, "message_en": e.message_en}), 400
        except Exception as e:
            logger.exception(f"got exception from route: {str(e)}")
            raise e

        if res is None:
            return jsonify({"status": status})
        else:
            return jsonify({
                "data": res,
                "status": status
            })

    return wrapper


DEFAULT_WHERE = object()


def identity(x):
    return x


@dataclass
class Column:
    '''Name of the corresponding column in the database table'''
    db_column: str
    '''Type of the field. If set to Decimal or DateTime then read and write will be automatically filled with sensible defaults (unless overriden manually)'''
    dtype: Optional[Type] = None
    '''Functions which is run on every value that is read from the database. If None, the field will not be read from the database.'''
    read: Optional[Callable] = identity
    '''Functions which is run on every value that is written to the database. If None, the field cannot be written to.'''
    write: Optional[Callable] = identity
    '''Name of the column in the exposed API. If None, it will be the same as db_column'''
    exposed_name: Optional[str] = None
    '''Name alias which can be used in filters'''
    alias: Optional[str] = None

    def __post_init__(self):
        self.exposed_name = self.exposed_name or self.db_column
        if self.dtype == datetime:
            self.read = (lambda x: None if x is None else x.isoformat()) if self.read == identity else self.read
            self.write = (lambda x: None if x is None else parser.parse(x)) if self.write == identity else self.write
        elif self.dtype == Decimal:
            self.read = (lambda x: str(x)) if self.read == identity else self.read
            self.write = (lambda x: Decimal(str(x))) if self.write == identity else self.write


class Entity:
    def __init__(self, table, columns, allow_delete=True):
        '''
        table: The name of the table in the database.
        columns: List of column names in the database (excluding the id column which is implicit).
        allow_delete: Allow deleting an entity in the database. Or false, trying to call delete will raise a MethodNotAllowed exception.
        '''
        self.table = table
        self.columns = [Column(c) if isinstance(c, str) else c for c in columns]

        if "id" not in [c.db_column for c in self.columns]:
            self.columns.insert(0, Column("id"))

        for c in self.columns:
            c.exposed_name = c.exposed_name or c.db_column
            # Override settings in existing id column
            if c.db_column == "id":
                c.write = None
                c.alias = c.alias or "entity_id"

        self._readable = [c for c in self.columns if c.read is not None]
        self._writeable = [c for c in self.columns if c.write is not None]
        self.db = None
        self.allow_delete = allow_delete

        self._read_fields = ",".join(c.db_column for c in self._readable)

    def get(self, id):
        with self.db.cursor() as cur:
            cur.execute(f"SELECT {self._read_fields} FROM {self.table} WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                raise NotFound(f"No item with id '{id}' in table {self.table}")

            return self._convert_to_dict(item)

    def _convert_to_row(self, data, fields):
        for c in fields:
            if c.exposed_name not in data:
                raise MissingFieldException(c.exposed_name)
        return [c.write(data[c.exposed_name]) for c in fields]

    def _convert_to_dict(self, row):
        assert len(row) == len(self._readable)
        return {c.exposed_name: c.read(item) for c, item in zip(self._readable, row)}

    def put(self, data, id):
        # Allow updating only a few fields
        # Check which fields the object has, and update only those
        fields = [col for col in self._writeable if col.exposed_name in data]
        if len(fields) == 0:
            abort(400, "No matching fields in the data, are you field names correct?")

        with self.db.cursor() as cur:
            values = self._convert_to_row(data, fields)
            cols = ','.join(col.db_column + '=%s' for col in fields)
            cur.execute(f"UPDATE {self.table} SET {cols} WHERE id=%s", (*values, id))
            return self.get(id)

    def post(self, data):
        with self.db.cursor() as cur:
            values = self._convert_to_row(data, self._writeable)
            cols = ','.join('%s' for col in self._writeable)
            write_fields = ",".join(c.db_column for c in self._writeable)
            cur.execute(f"INSERT INTO {self.table} ({write_fields}) VALUES({cols})", values)
            return self.get(cur.lastrowid)

    def delete(self, id):
        if not self.allow_delete:
            return MethodNotAllowed()

        with self.db.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET deleted_at=CURRENT_TIMESTAMP WHERE id=%s", (id,))

    def _format_column_filter(self, column, values):
        return (f"{column.db_column} in ({','.join(['%s'] * len(values))})", list(map(column.write or (lambda x: x), values)))

    def list(self, where=DEFAULT_WHERE, where_values=[]):
        if where == DEFAULT_WHERE:
            name2col = {c.exposed_name: c for c in self._readable}
            name2col.update({c.alias: c for c in self._readable if c.alias is not None})

            filter_data = [self._format_column_filter(name2col[key], value.split(",")) for key,value in request.args.items() if key in name2col]

            if self.allow_delete:
                filter_data.append(("deleted_at IS NULL", []))

            where = " and ".join(val[0] for val in filter_data)
            where_values = tuple(val_i for val in filter_data for val_i in val[1])

        with self.db.cursor() as cur:
            where = "WHERE " + where if where else ""
            sql = f"SELECT {self._read_fields} FROM {self.table} {where}"
            cur.execute(sql, where_values)
            rows = cur.fetchall()
            res = [self._convert_to_dict(row) for row in rows]
            return res

    def add_routes(self, service, endpoint, read_permission=DEFAULT_PERMISSION, write_permission=DEFAULT_PERMISSION, allow_post=True):
        # Note: Many methods here return other methods that we then call.
        # The endpoint keyword argument is just because flask needs something unique, it doesn't matter what it is for our purposes
        id_string = "<int:id>" if endpoint == "" else "/<int:id>"
        service.route(endpoint + id_string, endpoint=endpoint + "-get", methods=["GET"], permission=read_permission)(route_helper(self.get, status="ok"))
        service.route(endpoint + id_string, endpoint=endpoint + "-put", methods=["PUT"], permission=write_permission)(route_helper(self.put, json=True, status="updated"))
        if self.allow_delete:
            service.route(endpoint + id_string, endpoint=endpoint + "-delete", methods=["DELETE"], permission=write_permission)(route_helper(self.delete, status="deleted"))
        if allow_post:
            service.route(endpoint + "", endpoint=endpoint + "-post", methods=["POST"], permission=write_permission)(route_helper(self.post, json=True, status="created"))
        service.route(endpoint + "", endpoint=endpoint + "-list", methods=["GET"], permission=read_permission)(route_helper(self.list, status="ok"))
