from logging import ERROR

from flask import Response, jsonify

from service.logging import logger
from typing import Any, Optional, Tuple, Union


# Internal log level to error log with exception.
EXCEPTION = 333


GENERIC_500_ERROR_MESSAGE = "Something went wrong while trying to contact a service in our internal network."


def log(level: int, message: str) -> None:
    if level == EXCEPTION:
        logger.exception(message)
    else:
        logger.log(level, message)


def error_handler_db(error: "ApiError") -> Response:
    logger.exception(f"error when communicating with db: {str(error)}")
    response = jsonify(
        message=GENERIC_500_ERROR_MESSAGE,
        status="error",
        fields=None,
        what=None,
    )
    response.status_code = 500
    return response


def error_handler_api(error: "ApiError") -> Response:
    if error.log is True:
        log(error.level, repr(error))
    elif error.log:
        log(error.level, error.log)

    return error.to_response()


def error_handler_400(error: Any) -> Tuple[Response, int]:
    return jsonify(dict(message="Bad request.", status="error")), 400


def error_handler_404(error: Any) -> Tuple[Response, int]:
    return jsonify(dict(message="Not found.", status="error")), 404


def error_handler_405(error: Any) -> Tuple[Response, int]:
    return jsonify(dict(message="Method not allowed.", status="error")), 405


def error_handler_500(error: Any) -> Tuple[Response, int]:
    return jsonify(dict(message="Internal server error.", status="error")), 500


class ApiError(Exception):
    """Used for errors that should be communicated to the client as json payload, but also raised as results when
    communcating with external services. In that case the response is used to choose class and fill the data."""

    code = 400
    message: Optional[str] = None

    def __init__(
        self,
        message: Optional[str] = None,
        fields: Optional[str] = None,
        what: Optional[str] = None,
        status: str = "error",
        service: Optional[str] = None,
        code: Optional[int] = None,
        log: Optional[Union[str, bool]] = None,
        level: int = ERROR,
    ):
        """
        :param message human readable message of what went wrong, should be safe to show to end users
        :param status is this really needed? we have http status code
        :param service this external service created this response
        :param fields comma separated list of db fields/request parameters that was wrong, use when code is not enough
        :param what symbolic string of what went wrong, only use when code and field is not specific enough
        :param code http status code
        :param log log when responding, if True all content will be logged, if a string that string will be logged
        :param level use this level when logging, if EXCEPTION full exception is logged
        """
        if code:
            self.code = code
        if message:
            self.message = message
        self.status = status
        self.fields = fields
        self.what = what
        self.service = service
        self.log = log
        self.level = level

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(code={self.code}, status={self.status}, fields={self.fields}"
            f", what={self.what}, message='{self.message}, service='{self.service}')"
        )

    def to_response(self) -> Response:
        response = jsonify(
            message=self.message,
            fields=self.fields,
            what=self.what,
            status=self.status,
            service=self.service,
            # Legacy response fields, remove when not used any more.
            column=self.fields,
            type=self.what,
        )
        response.status_code = self.code
        return response


class BadRequest(ApiError):
    code = 400


class Unauthorized(ApiError):
    code = 401


class Forbidden(ApiError):
    code = 403


class NotFound(ApiError):
    code = 404


class PreconditionFailed(ApiError):
    code = 412


class TooManyRequests(ApiError):
    code = 429


class UnprocessableEntity(ApiError):
    code = 422


class InternalServerError(ApiError):
    code = 500


errors = {
    e.code: e
    for e in [BadRequest, Unauthorized, Forbidden, NotFound, TooManyRequests, UnprocessableEntity, InternalServerError]
}
