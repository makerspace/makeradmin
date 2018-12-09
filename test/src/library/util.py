import os
import sys
import time
from collections import Mapping
from functools import wraps
from random import seed, choice
from string import ascii_letters, digits

seed(os.urandom(8))


def random_str(length=12):
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


env = None


def get_env(name):
    """ Read variable from os environment, if not exists try to read from .env-file. Inside the test container the
    .env-file is not available all variables should be provided through the docker-compose.test.yml file. """
    
    global env
    if env is None:
        try:
            filename = os.path.abspath(f"{os.path.dirname(__file__)}/../../../.env")
            with open(filename) as f:
                env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}
        except OSError:
            env = {}
    
    if name in os.environ:
        return os.environ[name]
    
    return env[name]


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
    

def retry(timeout=2.0, sleep=0.2, do_retry=None):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrap(*args, **kwargs):
            start = time.perf_counter()
            while True:
                try:
                    wrapped(*args, **kwargs)
                except Exception as e:
                    elapsed = time.perf_counter() - start
                    if timeout < elapsed or not do_retry(e):
                        raise
                    print(f"{wrapped.__qualname__} failed with the following error after {elapsed:02f}s: {str(e)}",
                          file=sys.stderr)
                time.sleep(sleep)
        return wrap
    return decorator
    

