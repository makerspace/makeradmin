from collections import namedtuple
from service.external_service import ExternalService

import core


Instance = namedtuple("Instance", "path,service")


services = (
    Instance(path='', service=core.service),
    Instance(path='messages', service=ExternalService(name='messages', url='messages:80'))
)
