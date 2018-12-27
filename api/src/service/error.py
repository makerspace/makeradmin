from flask import jsonify


def error_handler(error):
    # TODO Maybe add a handler for db communication errors.
    response = jsonify(
        message=error.message,
        field=error.field,
        what=error.what,
        status=error.status,
    )
    response.status_code = error.code
    return response


class ApiError(Exception):
    code = 400

    def __init__(self, message=None, field=None, what=None, status="error", code=None):
        if code: self.code = code
        self.status = status
        self.message = message
        self.field = field
        self.what = what
        # TODO How to do translated messages? Do we do only message keys?
        
        
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
