from collections import namedtuple

import membership
import core
import messages
import multiaccess
from service.config import config
from service.external_service import ExternalService

Instance = namedtuple("Instance", "path,service")


services = (
    Instance(path='', service=core.service),
    Instance(path='/membership', service=membership.service),
    Instance(path='/webshop', service=ExternalService('webshop', config.get('SHOP_URL'))),
    Instance(path='/member', service=member.service),
    Instance(path='/messages', service=messages.service),
    Instance(path='/statistics', service=ExternalService('statistics', config.get('STATISTICS_URL'))),
    Instance(path='/multiaccess', service=multiaccess.service)
)
