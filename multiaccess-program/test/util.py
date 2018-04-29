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


def dt_cet_local(dt):
    """ Convert dt with timezone to a time in cet in local time. """
    return cet.localize(dt).replace(tzinfo=None)


def dt_cet(dt):
    """ Return unlocalized datetime as CET. """
    return cet.localize(dt)


def dt_format(dt):
    return dt.astimezone(utc).strftime(dt_utc_fmt)
    