import json
from requests import Response, PreparedRequest
from flask import g, request, Request as FlaskRequest
from flask.wrappers import Response as FlaskResponse
from datetime import datetime


def byte_decode(data: bytes):
    return data.decode('utf-8', 'backslashreplace')


class TrafficLogger:
    LOG_LIMIT = 64 * 1024

    def __init__(self):
        self.create_time = datetime.utcnow().isoformat()+'Z'
        self.service_traffic = list()

    def log_service_traffic(self, traffic: Response):
        req: PreparedRequest = traffic.request
        req_body = byte_decode(req.body) if type(req.body) == bytes else req.body

        req_data = {
            "method": req.method,
            "url": req.url,
            "headers": dict(req.headers),
            "body": req_body
        }
        resp_data = {
            "status": traffic.status_code,
            "headers": dict(traffic.headers),
            "data": traffic.text if len(traffic.content) < self.LOG_LIMIT else "<content too large for logging>"
        }
        self.service_traffic.append({
            "timeElapsed": traffic.elapsed.total_seconds(),
            "request": req_data,
            "response": resp_data
        })

    def commit(self, session_request: FlaskRequest, session_response: FlaskResponse):
        method = session_request.method
        session_request_data = {
            "date": self.create_time,
            "method": method,
            "url": session_request.path,
            "headers": dict(session_request.headers),
            "query": session_request.args,
        }
        if method != "GET":
            session_request_data["data"] = (
                session_request.get_json() if session_request.is_json and session_request.content_length
                else session_request.get_data(as_text=True) if session_request.content_length or 0 < self.LOG_LIMIT
                else "<content too large for logging>"
            )
        session_response_data = {
            "date": datetime.utcnow().isoformat()+'Z',
            "status": session_response.status_code,
            "headers": dict(session_response.headers),
            "data": byte_decode(session_response.data),
        }
        traffic_data = {
            "ip": session_request.remote_addr,
            "host": session_request.host,
            "request": session_request_data,
            "service_traffic": self.service_traffic,
            "response": session_response_data
        }
        with open(f"/work/logs/{self.create_time}_{session_request.remote_addr}_{method}.json", "w") as file:
            json.dump(traffic_data, file, ensure_ascii=False)


def traffic_logger_init():
    """ Add TrafficLogger instance to global object. """

    # Create traffic logger object.
    g.traffic_logger = TrafficLogger()


def log_traffic(traffic: Response):
    """ Log traffic to global object. """

    traffic_logger: TrafficLogger = g.traffic_logger
    traffic_logger.log_service_traffic(traffic)


def traffic_logger_commit(response: FlaskResponse):
    """ Write TrafficLogger data. """

    traffic_logger: TrafficLogger = g.traffic_logger
    traffic_logger.commit(request, response)
