from datetime import time, datetime

from pytz import timezone

#TODO remove things we dont need here

class classinstancemethod(object):
    """ Decorator for methods that can be used both in a class or instance contex. The first argument will be either
    class or object, depending on how the method was called. """

    def __init__(self, method):
        self.method = method

    def __get__(self, obj, typ=None):
        def wrap(*args, **kwargs):
            return self.method(obj or typ, *args, **kwargs)
        return wrap


cet = timezone("Europe/Stockholm")
utc = timezone("UTC")


def cet_to_utc(dt):
    """ Convert a naive dt in cet to naive dt in utc. """
    assert not dt.tzinfo
    return cet.localize(dt, is_dst=None).astimezone(utc).replace(tzinfo=None)


def to_cet_23_59_59(d):
    """ Convert a date with timezone to naive dt in cet 23:59:59. """
    if d is None:
        return None
    return datetime.combine(d, time(23, 59, 59))


def date_parse(s):
    """ Parse a date from maker admin. """
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()
    

def dt_format(dt):
    """ Format dt in utc to something that maker admin can parse. """
    assert not dt.tzinfo or dt.tzinfo == utc
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    