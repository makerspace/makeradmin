import stripe

from service.internal_service import InternalService
from service.config import config

stripe.api_version = '2022-11-15'
service = InternalService(name='shop')


import shop.views
