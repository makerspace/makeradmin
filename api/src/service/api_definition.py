
# HTTP Methods
import re
from inspect import signature

from flask import request

from service.error import ApiError

POST = 'POST'
GET = 'GET'
DELETE = 'DELETE'
PUT = 'PUT'

# Permissions
PUBLIC = 'public'
SERVICE = 'service'


# TODO Param (http) or arg (flask), how are post parameters handled in flask?
class Arg:
    """ Use as default argument on route to parse post args/url parameters into keyword arguments. """
    
    def __init__(self, converter, required=True):
        """
        :param converter converter function from string for the arg, any exception will render a 400 response
        :param required set to true if this is a required arg
        """
        self.converter = converter
        self.required = required
    
    def __bool__(self):
        return False
    
    @staticmethod
    def get_args(func):
        """ Return a dict with args defined as default values in a functions keyword arguments. """
        res = {}
        for name, parameter in signature(func).parameters.items():
            if isinstance(parameter.default, Arg):
                res[name] = parameter.default
        return res
    
    @staticmethod
    def fill_args(args, kwargs):
        """ Fill params from request in kwargs, raises bad request on validation errors. """
        for name, param in args.items():
            value = request.args.get(name)
            if value is None and param.required:
                raise ApiError(message=f'parameter {name} is required')
            try:
                value = param.converter(value)
            except Exception as e:
                raise ApiError(arg=name, message=f'failed to validate parameter {name}: {str(e)}')
            kwargs[name] = value


def symbol(value):
    """ A string of only ascii aplhanum and _. """
    if not re.match(r'[A-Za-z0-9_]+', value):
        raise ValueError(f"'{value}' is not symbolic")
    return value
