import requests

from flask import Blueprint, g, request
from requests import RequestException

from service.api_definition import POST, SERVICE_USER_ID, SERVICE_PERMISSIONS, GET, PUT, DELETE
from service.error import InternalServerError, ApiError, EXCEPTION, GENERIC_ERROR_MESSAGE
from service.logging import logger


class ExternalService(Blueprint):
    """ Flask blueprint for external services that sends all requests to an external service. Authentication is done
    here and permission information is forwarded as HTTP headers. """
    
    def __init__(self, name, url):
        super().__init__(name, name)
        self.name = name
        self.url = url

        @self.route("/", methods=(GET, PUT, POST, DELETE))
        @self.route("/<path:path>", methods=(GET, PUT, POST, DELETE))
        def upstream_service(path=""):
            logger.info(f"forwarding to external service at {self.url}/{self.name}/{path}")
            response = self.raw_request('/' + path, request.method, data=request.get_data())
            return response.content, response.status_code
        
    def migrate(self, *args, **kwargs):
        pass

    def raw_request(self, path, method, user_id=None, permissions=None, **kwargs):
        user_id = user_id or g.user_id
        permissions = permissions or g.permissions
        
        url = f"{self.url}/{self.name}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers={
                    'X-User-Id': str(user_id),
                    'X-User-Permissions': ','.join(permissions),
                },
                timeout=4,
                **kwargs,
            )
        except RequestException as e:
            raise InternalServerError(GENERIC_ERROR_MESSAGE, log=f"{method} to {url} failed: {str(e)}", level=EXCEPTION)

        return response

    def request(self, path, method, **kwargs):
        response = self.raw_request(path, method, **kwargs)
        
        if response.status_code >= 500:
            raise ApiError.parse(response, message=GENERIC_ERROR_MESSAGE, log=f"{method} to {url} failed")
        
        if response.status_code >= 400:
            raise ApiError.parse(response)

        data = response.json()
        
        return data.get('data')

    def user_post(self, path, **data):
        return self.request(path, method=POST, data=data)

    def service_post(self, path, **data):
        return self.request(path, method=POST, data=data, user_id=SERVICE_USER_ID, permissions=SERVICE_PERMISSIONS)

    def user_get(self, path):
        return self.request(path, method=GET)

    def service_get(self, path):
        return self.request(path, method=GET, user_id=SERVICE_USER_ID, permissions=SERVICE_PERMISSIONS)
