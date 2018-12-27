import requests

from flask import Blueprint
from requests import RequestException

from service.api_definition import SERVICE
from service.error import InternalServerError, ApiError
from service.logging import logger


GENERIC_ERROR_MESSAGE = "Something went wrong while trying to contact a service in our internal network."


class ExternalService(Blueprint):
    """ Flask blueprint for external services that sends all requests to an external service. Authentication is done
    here and permission information is forwarded as HTTP headers. """
    
    def __init__(self, name, url):
        super().__init__(name, name)
        self.name = name
        self.url = url
        
    def migrate(self, *args, **kwargs):
        pass

    def post(self, path, user_id=-1, permission=SERVICE, **data):
        url = f"http://{self.url}/{self.name}{path}"
        try:
            response = requests.post(
                url=url,
                data=data,
                headers={
                    'X-User-Id': str(user_id),
                    'X-User-Permissions': permission,
                },
                timeout=4,
            )
        except RequestException as e:
            logger.exception(f"failed to post to {url}: {str(e)}")
            raise InternalServerError(GENERIC_ERROR_MESSAGE)
        
        if response.status_code > 499:
            raise ApiError(code=response.status_code, message=GENERIC_ERROR_MESSAGE)

        data = response.json()
        
        if response.status_code > 399:
            raise ApiError(code=response.status_code, status=data.get('status'), message=data.get('message'),
                           field=data.get('column'), what=data.get('type'))
        
        return data.get('data')
        
