import stripe

from service.config import config

stripe.api_key = config.get("STRIPE_PRIVATE_KEY", log_value=False)

# All stripe calculations are done with cents (ören in Sweden)
STRIPE_CURRENTY_BASE = 100

CURRENCY = "sek"

STRIPE_SIGNING_SECRET = config.get("STRIPE_SIGNING_SECRET", log_value=False)


class Type:
    SOURCE = 'source'
    CARD = 'card'
    CHARGE = 'charge'


class Subtype:
    CHARGABLE = 'chargeable'
    FAILED = 'failed'
    CANCELED = 'canceled'
    SUCCEEDED = 'succeeded'
    DISPUTE_PREFIX = 'dispute'
    REFUND_PREFIX = 'refund'


class SourceType:
    THREE_D_SECURE = 'three_d_secure'
    CARD = 'card'


class SourceStatus:
    CHARGEABLE = 'chargeable'
    CONSUMED = 'consumed'
    FAILED = 'failed'
    PENDING = "pending"


class SourceRedirectStatus:
    PENDING = 'pending'
    NOT_REQUIRED = 'not_required'


class ChargeStatus:
    SUCCEEDED = 'succeeded'

