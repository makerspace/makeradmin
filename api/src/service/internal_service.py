import re
from functools import wraps, partial

import pymysql
from flask import Blueprint, g, jsonify
from pymysql.constants.ER import DUP_ENTRY, BAD_NULL_ERROR
from sqlalchemy.exc import IntegrityError

from service.api_definition import Arg, PUBLIC, GET, POST, PUT, DELETE, SERVICE, USER, REQUIRED, NOT_UNIQUE
from service.db import db_session, fields_by_index
from service.error import Forbidden, UnprocessableEntity
from service.logging import logger


class InternalService(Blueprint):
    """ Flask blueprint for internal service that handles requests within the same process, authentication and
    permissions is handled by this class. """
    
    def __init__(self, name):
        """
        The name of the service, this should be __name__.
        """
        
        super().__init__(name, name)

    def route(self, path, permission=None, method=None, methods=None, status='ok', code=200,
              commit=True, commit_on_error=False, flat_return=False, **route_kwargs):
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
        :param commit_on_error commit db_session even if there was an exception
        :param route_kwargs all extra kwargs are forwarded to Blueprint.route
        :param flat_return some endpoints returns data flattened
        """
        
        assert permission is not None, "permission is required, use PUBLIC for no permission needed"
        assert bool(method) != bool(methods), "exactly one of method and methods parameter should be set"

        methods = methods or (method,)
        
        def decorator(f):
            params = Arg.get_args(f)
            
            @wraps(f)
            def view_wrapper(*args, **kwargs):
                try:
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
                    
                    if commit and not commit_on_error:
                        db_session.commit()
                        
                except IntegrityError as e:
                    if isinstance(e.orig, pymysql.err.IntegrityError):
                        # This parsing of db errors is very sketchy, but there are tests for it so at least we know
                        # if it stops working.
                        errno, error = e.orig.args
                        if errno == DUP_ENTRY:
                            m = re.match(r".*?'([^']*)'.*?'([^']*)'.*", error)
                            if m:
                                value = m.group(1)
                                index = m.group(2)
                                try:
                                    fields = fields_by_index[index]
                                    raise UnprocessableEntity(f"Duplicate '{fields}', '{value}' already exists.",
                                                              what=NOT_UNIQUE, fields=fields)
                                except KeyError:
                                    logger.warning(f"index {index} is missing in index to fields mapping")
                                    raise UnprocessableEntity(f"Duplicate '{value}' not allowed.", what=NOT_UNIQUE)
                            else:
                                raise UnprocessableEntity(f"Duplicate entry.", what=NOT_UNIQUE)
                        
                        if errno == BAD_NULL_ERROR:
                            m = re.match(r".*?'([^']*)'.*", error)
                            if m:
                                field = m.group(1)
                            else:
                                field = None
                            
                            raise UnprocessableEntity(f"'{field}' is required." if field else "Required field missing.",
                                                      fields=field, what=REQUIRED)
                        
                    raise UnprocessableEntity("Could not save entity using the sent data.",
                                              log=f"unrecoginized integrity error: {str(e)}")
                
                finally:
                    if commit_on_error:
                        db_session.commit()
                
                return result
            
            return super(InternalService, self).route(path, methods=methods, **route_kwargs)(view_wrapper)
        return decorator
    
    def entity_routes(self, path=None, entity=None, permission_list=None, permission_create=None, permission_read=None,
                      permission_update=None, permission_delete=None):
        """
        Add routes to manipulate an entity (model). Routes will be added if there is a permission for it,
        list: GET <path>, create: POST <path>, update: PUT <path>/<id>, read: GET <path>/<id>, delete: DELETE
        <path>/<id>.
        
        :param path path to use for entity
        :param entity object which supports the view methods needed
        :param permission_list permission needed to list
        :param permission_create permission needed to create
        :param permission_read permission needed to read
        :param permission_update permission needed to update
        :param permission_delete permission needed to delete
        """
        
        if permission_list:
            self.route(
                path,
                endpoint=entity.name + "_list",
                permission=permission_list,
                method=GET,
                flat_return=True,
            )(entity.list)
        
        if permission_create:
            self.route(
                path,
                endpoint=entity.name + "_create",
                permission=permission_create,
                method=POST,
                status='created',
                code=201,
            )(entity.create)

        if permission_read:
            self.route(
                f"{path}/<int:entity_id>",
                endpoint=entity.name + "_read",
                permission=permission_read,
                method=GET,
            )(entity.read)

        if permission_update:
            self.route(
                f"{path}/<int:entity_id>",
                endpoint=entity.name + "_update",
                permission=permission_update,
                method=PUT,
                status='updated',
            )(entity.update)

        if permission_delete:
            self.route(
                f"{path}/<int:entity_id>",
                endpoint=entity.name + "_delete",
                permission=permission_delete,
                method=DELETE,
                status='deleted',
            )(entity.delete)

    def related_entity_routes(self, path=None, entity=None, relation=None,
                              permission_list=None, permission_add=None, permission_remove=None):
        """
        Add routes to manipulate entity (model) related to another entity. Path must contain <int:related_entity_id>
        for where the related entity id should be entered. Routes will be added if there is a permission for it,
        list: GET <path>, add: POST <path>/add, remove: POST <path>/remove.
        
        :param path path to use for entity, have to contain <int:related_entity_id>
        :param entity object which supports the view methods needed, this object will be returned by list
        :param relation object used together with entity to implement the operations
        :param permission_list permission needed to list
        :param permission_add permission needed to add to relation
        :param permission_remove permission needed to remove from relation
        """
        
        if permission_list:
            self.route(
                path,
                endpoint=f"{entity.name}_{relation.name}_list",
                permission=permission_list,
                method=GET,
                flat_return=True,
            )(partial(entity.list, relation=relation))
        
        if permission_add:
            self.route(
                f"{path}/add",
                endpoint=f"{entity.name}_{relation.name}_add",
                permission=permission_add,
                method=POST,
                code=200,
            )(partial(entity.related_add, relation=relation))

        if permission_remove:
            self.route(
                f"{path}/remove",
                endpoint=f"{entity.name}_{relation.name}_remove",
                permission=permission_remove,
                method=POST,
            )(partial(entity.related_remove, relation=relation))
