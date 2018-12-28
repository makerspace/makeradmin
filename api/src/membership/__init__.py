from service.config import config
from service.external_service import ExternalService


host = config.get('MEMBERSHIP_HOST')
port = int(config.get('MEMBERSHIP_PORT'))

service = ExternalService(name='membership', url=f"http://{host}:{port}")
