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
    PAYMENT_INTENT = 'payment_intent'


class Subtype:
    CHARGEABLE = 'chargeable'
    FAILED = 'failed'
    CANCELED = 'canceled'
    SUCCEEDED = 'succeeded'
    DISPUTE_PREFIX = 'dispute'
    REFUND_PREFIX = 'refund'
    PAYMENT_FAILED = 'payment_failed'


class SourceType:
    THREE_D_SECURE = 'three_d_secure'
    CARD = 'card'


class ChargeStatus:
    SUCCEEDED = 'succeeded'


class PaymentIntentStatus:
    REQUIRES_PAYMENT_METHOD = 'requires_payment_method'
    REQUIRES_CONFIRMATION = 'requires_confirmation'
    REQUIRES_ACTION = 'requires_action'
    PROCESSING = 'processing'
    CANCELED = 'canceled'
    SUCCEEDED = 'succeeded'
    REQUIRES_CAPTURE = 'requires_capture'


class PaymentIntentNextActionType:
    USE_STRIPE_SDK = 'use_stripe_sdk'
    REDIRECT_TO_URL = 'redirect_to_url'
