import stripe

from service.internal_service import InternalService
from service.config import config


service = InternalService(name='shop')


import shop.views
