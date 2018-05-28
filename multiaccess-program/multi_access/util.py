from datetime import datetime

from pytz import timezone


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
dt_utc_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'


def cet_to_utc(dt):
    """ Convert a naive dt in cet to naive time in utc. """
    return cet.localize(dt, is_dst=None).astimezone(utc).replace(tzinfo=None)


def dt_parse(s):
    """ Parse a string standard maker admin format in utc without timezone. """
    return datetime.strptime(s, dt_utc_fmt)
    

def dt_format(dt):
    """ Format dt in utc in maker admin standard format. """
    assert not dt.tzinfo or dt.tzinfo == utc
    return dt.strftime(dt_utc_fmt)
    