import stripe

from service.internal_service import InternalService
from service.config import config


stripe.api_key = config.get("STRIPE_PRIVATE_KEY", log_value=False)


service = InternalService(name='shop')


import shop.views
