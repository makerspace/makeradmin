from service.config import config
from service.external_service import ExternalService


service = ExternalService(name='membership', url=config.get('MEMBERSHIP_URL'))
