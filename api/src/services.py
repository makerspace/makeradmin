from collections import namedtuple

import membership
import core
from service.config import config
from service.external_service import ExternalService

Instance = namedtuple("Instance", "path,service")


services = (
    Instance(path='', service=core.service),
    Instance(path='/membership', service=membership.service),
    Instance(path='/webshop', service=ExternalService('webshop', config.get('SHOP_URL'))),
    Instance(path='/member', service=ExternalService('member', config.get('MEMBER_URL'))),
    Instance(path='/messages', service=ExternalService('messages', config.get('MESSAGES_URL'))),
    Instance(path='/email-dispatcher', service=ExternalService('email-dispatcher', config.get('EMAIL_DISPATCHER_URL'))),
    Instance(path='/multiaccesssync', service=ExternalService('multiaccesssync', config.get('MULTIACCESS_SYNC_URL'))),
)

