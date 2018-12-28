from logging import ERROR, CRITICAL

from flask import jsonify

from service.logging import logger


def log(level, message):
    if level == CRITICAL:
        logger.exception(message)
    else:
        logger.log(level, message)


def error_handler(error):
    # TODO Maybe add a handler for db communication errors.
    
    if error.log is True:
        logger.log(error.level, repr(error))
    elif error.log:
        logger.log(error.level, error.log)
    # TODO Remove this logging if it turns out to be used in too few places.
        
    return error.to_response()


class ApiError(Exception):
    """ Used for errors that should be communicated to the client as json payload, but also raised as results when
    communcating with external services. In that case the response is used to choose class and fill the data.  """
    
    code = 400

    def __init__(self, message=None, fields=None, what=None, status="error", code=None, log=None, level=ERROR):
        """
        :param message human readable message of what went wrong, should be safe to show to end users
        :param status TODO is this really needed? we have http status code
        :param fields comma separated list of db fields/request parameters that was wrong
        :param what symbolic string of what went wrong
        :param code http status code
        :param log log when responding, if True all content will be logged, if a string that string will be logged
        :param level use this level when logging, if CRITICAL full exception is logged
        """
        if code: self.code = code
        self.status = status
        self.message = message
        self.fields = fields
        self.what = what
        self.log = log
        self.level = level
        # TODO How to do translated messages? Do we do only message keys?
        
    def __repr__(self):
        return f"{self.__class__.__name__}(code={self.code}, status={self.status}, fields={self.fields}" \
               f", what={self.what}, message='{self.message}')"
    
    def to_response(self):
        response = jsonify(
            message=self.message,
            fields=self.fields,
            what=self.what,
            status=self.status,
        )
        response.status_code = self.code
        return response

    @staticmethod
    def parse(response, **kwargs):
        """
        Parse a response object into the best matching exception object.
        
        :param kwargs ovverride constructor parameters with keyword arguments
        """
        cls = errors.get(response.status_code, ApiError)
        data = response.json()
        kwargs.setdefault('code', response.status_code)
        for key in ('message', 'fields', 'what', 'status'):
            kwargs.setdefault(key, data.get(key))
        return cls(**kwargs)


class BadRequest(ApiError):
    code = 400


class Unauthorized(ApiError):
    code = 401
    
    
class Forbidden(ApiError):
    code = 403


class TooManyRequests(ApiError):
    code = 429


class UnprocessableEntity(ApiError):
    code = 422


class InternalServerError(ApiError):
    code = 500


errors = {e.code: e for e in [BadRequest, Unauthorized, Forbidden, TooManyRequests, UnprocessableEntity,
                              InternalServerError]}