from flask import jsonify


def error_handler(error):
    response = error.data
    response.status_code = error.code
    return response


class ApiError(Exception):
    code = 400

    def __init__(self, code=None, arg=None, message=None):
        if code: self.code = code
        self.data = jsonify(status="error", arg=arg, message=message)
        # TODO How to do api errors?
        # TODO How to do translated messages?
        # TODO Do we do only message keys?
        
        
class PermissionDenied(ApiError):
    code = 403
