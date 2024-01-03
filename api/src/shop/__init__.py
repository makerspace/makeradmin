import stripe
from service.config import config
from service.internal_service import InternalService

service = InternalService(name="shop")


import shop.views
