import os
from collections.abc import Mapping
from random import seed, choice
from string import ascii_letters, digits


seed(os.urandom(8))


def random_str(length: int=12) -> str:
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


def get_path(obj, path):
    """ Return value from path in obj or None. """
    for seg in path.split('__'):
        try:
            obj = obj[seg]
        except (AttributeError, TypeError, KeyError):
            return None
    return obj
    
    
def merge_paths(**kwargs):
    """
    Return dict of path => value with paths on the form segment__segment__segment built by merging kwargs where each
    kwarg can be a full path, a partial path ending in a dict of paths or a dict. If there are conflicts the last
    value will be used.
    
    Examples:
        megrge_paths(a__path=1, a={'b': 2}, {'c': 3}) => {'a__path': 1, 'a__b': 2, 'c': 3}
        megrge_paths(a__path=1, a={'path': 2}) => {'a__path': 2}
    """
    res = {}
    
    def flatten(key, obj):
        if isinstance(obj, Mapping):
            for k, o in obj.items():
                flatten(f"{key}__{k}", o)
        else:
            res[key] = obj
    
    for key, obj in kwargs.items():
        flatten(key, obj)
    
    return res
    
    
class classinstancemethod(object):
    """ Decorator for methods that can be used both in a class or instance contex. The first argument will be either
    class or object, depending on how the method was called. """

    def __init__(self, method):
        self.method = method

    def __get__(self, obj, typ=None):
        def wrap(*args, **kwargs):
            return self.method(obj or typ, *args, **kwargs)
        return wrap

