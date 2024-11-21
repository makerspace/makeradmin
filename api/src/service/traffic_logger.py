import json
from datetime import datetime, timezone
from typing import List

from flask import Request as FlaskRequest
from flask import g, request
from flask.wrappers import Response as FlaskResponse
from requests import PreparedRequest, Response


def byte_decode(data: bytes) -> str:
    return data.decode("utf-8", "backslashreplace")


LOGGING_ENABLED = False


class TrafficLogger:
    LOG_LIMIT = 64 * 1024
    service_traffic: List[object]

    def __init__(self) -> None:
        self.create_time = datetime.now(timezone.utc).isoformat() + "Z"
        self.service_traffic = list()

    def log_service_traffic(self, traffic: Response) -> None:
        req: PreparedRequest = traffic.request
        req_body = byte_decode(req.body) if isinstance(req.body, bytes) else req.body

        req_data = {"method": req.method, "url": req.url, "headers": dict(req.headers), "body": req_body}
        resp_data = {
            "status": traffic.status_code,
            "headers": dict(traffic.headers),
            "data": traffic.text if len(traffic.content) < self.LOG_LIMIT else "<content too large for logging>",
        }
        self.service_traffic.append(
            {"timeElapsed": traffic.elapsed.total_seconds(), "request": req_data, "response": resp_data}
        )

    def commit(self, session_request: FlaskRequest, session_response: FlaskResponse) -> None:
        method = session_request.method
        session_request_data = {
            "date": self.create_time,
            "method": method,
            "url": session_request.path,
            "headers": dict(session_request.headers),
            "query": session_request.args,
        }
        session_response_data = {
            "date": datetime.now(timezone.utc).isoformat() + "Z",
            "status": session_response.status_code,
            "headers": dict(session_response.headers),
        }

        if method == "GET":
            if len(session_response.data) > self.LOG_LIMIT:
                data = "<content too large for logging>"
            # Webship images are unnecessary and large
            elif session_request.path.startswith("/webshop/image/"):
                data = "<skipping image content>"
            else:
                data = byte_decode(session_response.data)
            session_response_data["data"] = data

        if method != "GET":
            if (session_request.content_length or 0) > self.LOG_LIMIT:
                data = "<content too large for logging>"
            else:
                data = session_request.get_data(as_text=True)
            session_request_data["data"] = data

        traffic_data = {
            "ip": session_request.remote_addr,
            "host": session_request.host,
            "request": session_request_data,
            "service_traffic": self.service_traffic,
            "response": session_response_data,
        }
        with open(f"/work/logs/{self.create_time}_{session_request.remote_addr}_{method}.json", "w") as file:
            json.dump(traffic_data, file, ensure_ascii=False)


def traffic_logger_init() -> None:
    """Add TrafficLogger instance to global object."""

    if LOGGING_ENABLED:
        # Create traffic logger object.
        g.traffic_logger = TrafficLogger()


def log_traffic(traffic: Response) -> None:
    """Log traffic to global object."""

    if LOGGING_ENABLED:
        traffic_logger: TrafficLogger = g.traffic_logger
        traffic_logger.log_service_traffic(traffic)


def traffic_logger_commit(response: FlaskResponse) -> None:
    """Write TrafficLogger data."""

    if LOGGING_ENABLED:
        traffic_logger: TrafficLogger = g.traffic_logger
        traffic_logger.commit(request, response)
