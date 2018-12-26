from collections import namedtuple

import core
from service.external_service import ExternalService


Instance = namedtuple("Service", "path,service")


services = (
    Instance(path='', service=core.service),
#    Instance(path='messages', service=ExternalService(name='messages', url='messages:80'))
)

