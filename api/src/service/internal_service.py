from functools import wraps
from inspect import getmodule, stack, getfile
from os.path import dirname, join, isdir, exists

from flask import Blueprint, g, jsonify

from service.api_definition import Arg, PUBLIC, GET, POST, PUT, DELETE, SERVICE, USER
from service.db import db_session
from service.error import Forbidden
from service.migrate import migrate_service


class InternalService(Blueprint):
    """ Flask blueprint for internal service that handles requests within the same process, authentication and
    permissions is handled by this class. """
    
    def __init__(self, name, migrations=True):
        """
        The name of the service, this should be __name__.
        
        :param migrations set to True if there is a migrations dir with migrations in this service
        """
        
        super().__init__(name, name)
        self.migrations = migrations
        self.service_module = getmodule(stack()[1][0])

    def migrate(self, session_factory):
        if self.migrations:
            service_package_dir = dirname(getfile(self.service_module))
            migrations_dir = join(service_package_dir, 'migrations')
            
            if not exists(migrations_dir) and not isdir(migrations_dir):
                raise Exception(f"service {self.name} migrations dir {migrations_dir} is missing")
            
            migrate_service(session_factory, self.name, migrations_dir)

    def route(self, path, permission=None, method=None, methods=None, status='ok', code=200, commit=True,
              flat_return=False, **route_kwargs):
        """
        Enhanced Blueprint.route for internal services. The function should return a jsonable structure that will
        be put in the data key in the response.
        
        Function args with default Arg object will be auto filled and validated from the request.
        
        Authorized user_id and permissions list will be set on the g object.
        
        :param path path from Blueprint.route
        :param permission the permission required for the user to access this route
        :param method same as methods=[method]
        :param methods methods from Blueprint.rote
        :param status status value of response
        :param code response code
        :param commit commit db_session just before returning if no exception was raised
        :param route_kwargs all extra kwargs are forwarded to Blueprint.route
        :param flat_return some endpoints returns data flattened, most don't TODO fix this
        """
        
        assert permission is not None, "permission is required, use PUBLIC for no permission needed"
        assert bool(method) != bool(methods), "exactly one of method and methods parameter should be set"
        
        methods = methods or (method,)
        
        def decorator(f):
            params = Arg.get_args(f)
            
            @wraps(f)
            def view_wrapper(*args, **kwargs):
                has_permission = (
                        permission == PUBLIC
                        or permission in g.permissions
                        or (SERVICE in g.permissions and permission != USER)
                )
                
                if not has_permission:
                    raise Forbidden(message=f"'{permission}' permission is required for this operation.")
                
                Arg.fill_args(params, kwargs)
                
                data = f(*args, **kwargs)
                
                if flat_return:
                    result = jsonify({**data, 'status': status}), code
                else:
                    result = jsonify({'status': status, 'data': data}), code
                
                if commit:
                    db_session.commit()
                
                return result
            
            return super(InternalService, self).route(path, methods=methods, **route_kwargs)(view_wrapper)
        return decorator
    
    def entity_routes(self, path=None, entity=None, permissions=None):
        """
        Add routes to manipulate an entity (model). Routes will be added if there is a permission for it,
        list: GET <path>, create: POST <path>, update: PUT <path>/<id>, read: GET <path>/<id>, delete: DELETE
        <path>/<id>.
        
        :param path path to use for entity
        :param entity object which supports the view methods needed
        :param permissions dict with keys list,read,write,create and delete if not set that route will not be created
        """
        
        list_permission = permissions.get('list')
        if list_permission:
            self.route(
                path, permission=list_permission, method=GET
            )(entity.list)
        
        create_permission = permissions.get('create')
        if create_permission:
            self.route(
                path, permission=create_permission, method=POST, status='created', code=201
            )(entity.create)

        read_permission = permissions.get('read')
        if read_permission:
            self.route(
                f"{path}/<int:entity_id>", permission=read_permission, method=GET
            )(entity.read)

        update_permission = permissions.get('update')
        if update_permission:
            self.route(
                f"{path}/<int:entity_id>", permission=update_permission, method=PUT, status='updated',
            )(entity.update)

        delete_permission = permissions.get('delete')
        if delete_permission:
            self.route(
                f"{path}/<int:entity_id>", permission=delete_permission, method=DELETE, status='deleted'
            )(entity.delete)
            
            