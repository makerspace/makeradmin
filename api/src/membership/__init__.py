from service.config import config
from service.external_service import ExternalService
from service.internal_service import InternalService

service = ExternalService(name='membership', url=config.get('MEMBERSHIP_URL'))
# service = InternalService(name='membership', migrations=True)
