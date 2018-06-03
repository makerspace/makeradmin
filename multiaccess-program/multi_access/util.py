import iso8601
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


def cet_to_utc(dt):
    """ Convert a naive dt in cet to naive dt in utc. """
    assert not dt.tzinfo
    return cet.localize(dt, is_dst=None).astimezone(utc).replace(tzinfo=None)


def to_cet(dt):
    """ Convert a datetime with timezone to naive dt in cet. """
    assert dt.tzinfo
    return dt.astimezone(cet).replace(tzinfo=None)


def dt_parse(s):
    """ Parse a datetime from maker admin with timezone offset. """
    dt = iso8601.parse_date(s)
    assert dt.tzinfo
    return dt
    

def dt_format(dt):
    """ Format dt in utc to something that maker admin can parse. """
    assert not dt.tzinfo or dt.tzinfo == utc
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    