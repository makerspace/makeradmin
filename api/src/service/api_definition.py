import re
from inspect import signature

from flask import request

from service.error import ApiError, UnprocessableEntity

# HTTP Methods
POST = 'post'
GET = 'get'
DELETE = 'delete'
PUT = 'put'

# TODO Since permissions are tied to the code it is probably better that they are in the code and not in the db. The
# db also contains a lot of unusable permissions. membership_group_permissions could contain permission enum/string
# directly.

# Special permissions
PUBLIC = 'public'    # Anyone on the internet can access this endpoint.
SERVICE = 'service'  # A service user (id < 0) needs to be authenticated, but no other permissions are needed.
USER = 'user'        # A regular user (id > 0) needs to be authenticated, but no other permissions are needed.

# Regular permissions
MEMBER_VIEW = 'member_view'
MEMBER_CREATE = 'member_create'
MEMBER_EDIT = 'member_edit'
MEMBER_DELETE = 'member_delete'
GROUP_VIEW = 'group_view'
GROUP_CREATE = 'group_create'
GROUP_EDIT = 'member_edit'
GROUP_DELETE = 'group_delete'
GROUP_MEMBER_VIEW = 'group_member_view'
GROUP_MEMBER_ADD = 'group_member_add'
GROUP_MEMBER_REMOVE = 'group_member_remove'
SPAN_VIEW = "span_view"
SPAN_MANAGE = "span_manage"

PERMISSION_VIEW = 'permission_view'
WEBSHOP = 'webshop'

# Service credentials
SERVICE_USER_ID = -1
SERVICE_PERMISSIONS = (SERVICE,)

# What
BAD_VALUE = 'bad_value'
REQUIRED = 'required'
EXPIRED = 'expired'
NOT_UNIQUE = 'not_unique'


class Arg:
    """ Use as default argument on route to parse parameters for the function from the request. It will try to get
    each argument from url parameters, then post form data, then json body. If a value is found it will be converted
    through a conversion function. """
    
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
            
            if value is None:
                value = request.form.get(name)
                
            if value is None:
                try:
                    value = request.get_json(silent=True).get(name)
                except AttributeError:
                    pass
            
            if value is None:
                if param.required:
                    raise ApiError(message=f'Parameter {name} is required.', fields=name, what=REQUIRED)
            
            else:
                try:
                    value = param.converter(value)
                except Exception as e:
                    raise UnprocessableEntity(fields=name, what=BAD_VALUE,
                                              message=f'Failed to validate parameter {name}: {str(e)}')
                
            kwargs[name] = value


class Enum:
    """ A string among a set of strings. """
    def __init__(self, *values):
        self.values = values
        
    def __call__(self, value):
        if value in self.values:
            return value
        raise ValueError(f"Value {value} not among allowed values.")


symbol_regex = re.compile(r'[A-Za-z0-9_]+')


def symbol(value):
    """ A string which is only A-Za-z0-9 and _. """
    if not symbol_regex.match(value):
        raise ValueError(f"Value {value} is not a symbol.")
    return value


def natural0(value):
    """ Natural including 0. """
    value = int(value)
    if value < 0:
        raise ValueError(f"Value {value} should be 0 or higher.")
    return value
    

def natural1(value):
    """ Natural excluding 0. """
    value = int(value)
    if value < 1:
        raise ValueError(f"Value {value} should be 1 or higher.")
    return value
    
    