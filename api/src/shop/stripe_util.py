from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from decimal import Decimal
import random
import time
from logging import getLogger
from sqlalchemy import func
from typing import Any, Callable, Dict, TypeVar

from service.error import InternalServerError
from service.db import db_session
from shop.models import Product, ProductCategory
from shop.stripe_constants import (
    STRIPE_CURRENTY_BASE,
)
import stripe

logger = getLogger("makeradmin")


@dataclass
class StripeRecurring:
    interval: str
    interval_count: int


def are_metadata_dicts_equivalent(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    a = {k: v for k, v in a.items() if v != ""}
    b = {k: v for k, v in b.items() if v != ""}
    return a == b


def get_subscription_category() -> ProductCategory:
    offset = 0
    while True:
        with db_session.begin_nested():
            try:
                offset += 1
                category = (
                    db_session.query(ProductCategory).filter(ProductCategory.name == "Subscriptions").one_or_none()
                )
                if category is None:
                    category = ProductCategory(
                        name="Subscriptions",
                        display_order=(db_session.query(func.max(ProductCategory.display_order)).scalar() or 0)
                        + offset,
                    )
                    db_session.add(category)
                    db_session.flush()

                return category
            except Exception as e:
                # I think, if this setup happens inside a transaction, we may not be able to see another category with the same display order,
                # but we will still be prevented from creating a new one with that display order.
                # So we incrementally increase the display order until we find a free one.
                # This race condition will basically only happen when executing tests in parallel.
                # TODO: Can this be done in a better way?
                logger.info("Race condition when creating category. Trying again: ", e)


T = TypeVar("T")
MAX_TRIES = 10


def retry(f: Callable[[], T]) -> T:
    """Retries a stripe operation if it fails with a rate limit error."""
    its = 0
    while True:
        try:
            return f()
        except stripe.RateLimitError:
            its += 1
            if its > MAX_TRIES:
                raise
            # Retry.
            # Especially when starting a lot of parallel tests, we can get rate limit errors.
            time.sleep(1 * (1.5**its) * (1.0 + random.random()))


def stripe_amount_from_makeradmin_product(makeradmin_product: Product, recurring: StripeRecurring | None) -> int:
    if recurring:
        return convert_to_stripe_amount(makeradmin_product.price * recurring.interval_count)
    else:
        return convert_to_stripe_amount(makeradmin_product.price)


def convert_to_stripe_amount(amount: Decimal) -> int:
    """Convert decimal amount to stripe amount and return it. Fails if amount is not even cents (ören)."""
    stripe_amount = amount * STRIPE_CURRENTY_BASE
    if stripe_amount % 1 != 0:
        raise InternalServerError(
            message=f"The amount could not be converted to an even number of ören ({amount}).",
            log=f"Stripe amount not even number of ören, maybe some product has uneven ören.",
        )

    return int(stripe_amount)


def convert_from_stripe_amount(stripe_amount: int) -> Decimal:
    """Convert stripe amount to decimal amount and return it."""
    amount = ((Decimal(stripe_amount) / STRIPE_CURRENTY_BASE)).quantize(Decimal("0.01"))
    return amount


def event_semantic_time(event: stripe.Event) -> datetime:
    """
    This is the time when the event happens semantically. E.g. an invoice is created at exactly 00:00 on the first of the month.
    This may be different from the time when the event is created in Stripe. In particular, when using a test clock
    the event_created_time is still in real-time, but the event_semantic_time follows the test clock.

    Some events do not have a semantic time. In that case we fall back on the event's timestamp.
    """
    obj = event["data"]["object"]
    return datetime.fromtimestamp(obj["created"] if "created" in obj else event["created"], timezone.utc)


def replace_default_payment_method(customer_id: str, payment_method_id: str) -> None:
    retry(
        lambda: stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id},
        )
    )

    # Delete all previous payment methods to keep things clean
    for pm in stripe.PaymentMethod.list(customer=customer_id).auto_paging_iter():
        if pm.id != payment_method_id:
            retry(lambda: stripe.PaymentMethod.detach(pm.id))
