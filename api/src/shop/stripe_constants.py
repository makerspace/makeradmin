from enum import Enum
import stripe
from test_aid.systest_config import STRIPE_PRIVATE_KEY, STRIPE_PUBLIC_KEY

from service.config import config

stripe.api_version = "2022-11-15"
# All stripe calculations are done with cents (ören in Sweden)
STRIPE_CURRENTY_BASE = 100

CURRENCY = config.get("STRIPE_CURRENCY")

STRIPE_SIGNING_SECRET = config.get("STRIPE_SIGNING_SECRET", log_value=False)


def set_stripe_key(private: bool) -> None:
    stripe.api_key = STRIPE_PRIVATE_KEY if private else STRIPE_PUBLIC_KEY


set_stripe_key(private=True)


class MakerspaceMetadataKeys(Enum):
    """Keys used in the metadata for stripe objects, and in some cases, metadata for makerspace products in the webshop"""

    USER_ID = "makerspace_user_id"

    # The makerspace member number. This is only intended to be used for human-readable ids, and should not be used for any logic.
    # When writing code, use USER_ID instead.
    MEMBER_NUMBER = "makerspace_member_number"

    # Type of price. See PriceType
    PRICE_TYPE = "price_type"
    SUBSCRIPTION_TYPE = "subscription_type"
    TRANSACTION_IDS = "makerspace_transaction_ids"
    PENDING_MEMBER = "makerspace_pending_member"
    PRICE_LEVEL = "makerspace_price_level"
    PRODUCT_ID = "makerspace_product_id"

    # Used in the webshop for special products
    SPECIAL_PRODUCT_ID = "special_product_id"

    # A product may specify this to indicate which discounts are applicable.
    # If this is not specified, no discounts will apply.
    # The 'normal' price level is always allowed regardless of this setting.
    # For example, if ['low_income_discount'] is specified, then the product will be able
    # to be purchased with the low income discount, which reduces the price by a certain percentage.
    # Allowed values are the values of PriceLevel, except 'normal'.
    ALLOWED_PRICE_LEVELS = "allowed_price_levels"


class PriceType(str, Enum):
    BINDING_PERIOD = "binding_period"
    RECURRING = "recurring"
    REGULAR_PRODUCT = "regular_product"


class EventType(str, Enum):
    SOURCE = "source"
    CARD = "card"
    CHARGE = "charge"
    PAYMENT_INTENT = "payment_intent"
    CUSTOMER = "customer"
    INVOICE = "invoice"
    CHECKOUT = "checkout"
    SUBSCRIPTION_SCHEDULE = "subscription_schedule"
    TEST_HELPERS = "test_helpers"


class EventSubtype(str, Enum):
    CHARGEABLE = "chargeable"
    FAILED = "failed"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"
    DISPUTE_PREFIX = "dispute"
    REFUND_PREFIX = "refund"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAID = "paid"
    UNCOLLECTABLE = "marked_uncollectible"
    UPDATED = "updated"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_DELETED = "subscription.deleted"
    SESSION_COMPLETED = "session.completed"
    TEST_CLOCK_ADVANCING = "test_clock.advancing"
    CREATED = "created"
    RELEASED = "released"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    TRAILING = "trailing"


class SourceType(str, Enum):
    THREE_D_SECURE = "three_d_secure"
    CARD = "card"


class ChargeStatus(str, Enum):
    SUCCEEDED = "succeeded"
    PENDING = "pending"
    FAILED = "failed"


class PaymentIntentStatus(str, Enum):
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"
    REQUIRES_CAPTURE = "requires_capture"


class PaymentIntentNextActionType(str, Enum):
    USE_STRIPE_SDK = "use_stripe_sdk"
    REDIRECT_TO_URL = "redirect_to_url"


class SubscriptionScheduleStatus(str, Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    RELEASED = "released"
    CANCELED = "canceled"


class SetupIntentStatus(Enum):
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"


class SetupFutureUsage(str, Enum):
    OFF_SESSION = "off_session"
    ON_SESSION = "on_session"
