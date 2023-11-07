from datetime import datetime, timezone
from decimal import Decimal
import random
import time
from logging import getLogger
from typing import Callable, Optional, TypeVar

from service.error import InternalServerError
from shop.models import Product
from shop.stripe_constants import (
    STRIPE_CURRENTY_BASE,
    PriceType,
    CURRENCY,
)
import stripe

logger = getLogger("makeradmin")

CURRENCY = "sek"  # TODO fix this


# TODO cache?
def get_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    id = f'prod_{makeradmin_product["id"]}' if livemode else f'test_{makeradmin_product["id"]}'
    try:
        product = retry(lambda: stripe.Product.retrieve(id=id))
    except stripe.error.InvalidRequestError as e:
        logger.warning(
            f'failed to retrive product from stripe for makeradmin product with id {makeradmin_product["id"]}, {e}'
        )
        return None
    assert product.livemode == livemode
    return product


# TODO cache?
def get_stripe_prices(
    stripe_product: stripe.Product, filterInactive: bool = True, livemode: bool = False
) -> list[stripe.Price] | None:
    try:
        prices = list(retry(lambda: stripe.Price.list(product=stripe_product.stripe_id)))
        if filterInactive:
            prices = [p for p in prices if p["active"]]
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"failed to retrive prices from stripe for stripe product with id {stripe_product.id}, {e}")
        return None
    for p in prices:
        assert p.livemode == livemode
    return prices


def _create_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    id = f'prod_{makeradmin_product["id"]}' if livemode else f'test_{makeradmin_product["id"]}'
    stripe_product = retry(
        lambda: stripe.Product.create(
            id=id,
            name=makeradmin_product["name"],
            description=f'Created by Makeradmin, product id (#{makeradmin_product["id"]})',
        )
    )
    assert stripe_product.livemode == livemode
    return stripe_product


def _create_stripe_price(
    makeradmin_product: Product, stripe_product: stripe.Product, priceType: PriceType, livemode: bool = False
) -> stripe.Price | None:
    id = f'prod_{makeradmin_product["id"]}_{priceType}' if livemode else f'test_{makeradmin_product["id"]}_{priceType}'
    if "mån" in makeradmin_product["unit"] or "month" in makeradmin_product["unit"]:
        interval = "month"
    elif "år" in makeradmin_product["unit"] or "year" in makeradmin_product["unit"]:
        interval = "year"
    else:
        raise RuntimeError(
            f'Unexpected unit {makeradmin_product["unit"]} in makeradmin product {makeradmin_product["id"]}'
        )
    interval_count = makeradmin_product["smallest_multiple"]
    recurring = {"interval": interval, "interval_count": interval_count}
    stripe_price = retry(
        lambda: stripe.Price.create(
            nickname=id,
            product=stripe_product.id,
            unit_amount=convert_to_stripe_amount(makeradmin_product["price"] * interval_count),
            currency=CURRENCY,
            recurring=recurring,
            metadata={"price_type": priceType},
        )
    )
    assert stripe_price.livemode == livemode
    return stripe_price


def find_or_create_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    stripe_product = get_stripe_product(makeradmin_product, livemode)
    if stripe_product is None:
        return _create_stripe_product(makeradmin_product, livemode)
    else:
        if not stripe_product.active:
            retry(lambda: stripe.Product.modify(stripe_product.id, active=True))
        return stripe_product


def _find_price_type(stripe_prices: list[stripe.Price] | None, price_type: PriceType):
    if stripe_prices is None:
        return None
    for p in stripe_prices:
        if p.metadata["price_type"] == price_type.value:
            return p
    return None


def find_or_create_stripe_prices_for_product(
    makeradmin_product: Product, stripe_product: stripe.Product, livemode: bool = False
) -> list[stripe.Price] | None:
    interval_count = makeradmin_product["smallest_multiple"]
    stripe_prices = get_stripe_prices(stripe_product, filterInactive=False, livemode=livemode)

    stripe_price_recurring = _find_price_type(stripe_prices, PriceType.RECURRING)
    if stripe_price_recurring is None:
        stripe_price_recurring = _create_stripe_price(makeradmin_product, stripe_product, PriceType.RECURRING, livemode)

    if interval_count == 1:
        return [stripe_price_recurring]

    stripe_price_binding = _find_price_type(stripe_prices, PriceType.RECURRING)
    if stripe_price_binding is None:
        stripe_price_binding = _create_stripe_price(
            makeradmin_product, stripe_product, PriceType.BINDING_PERIOD, livemode
        )

    return [stripe_price_recurring, stripe_price_recurring]


def convert_to_stripe_amount(amount: Decimal) -> int:
    """Convert decimal amount to stripe amount and return it. Fails if amount is not even cents (ören)."""
    stripe_amount = amount * STRIPE_CURRENTY_BASE
    if stripe_amount % 1 != 0:
        raise InternalServerError(
            message=f"The amount could not be converted to an even number of ören ({amount}).",
            log=f"Stripe amount not even number of ören, maybe some product has uneven ören.",
        )

    return int(stripe_amount)


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
    stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )

    # Delete all previous payment methods to keep things clean
    for pm in stripe.PaymentMethod.list(customer=customer_id).auto_paging_iter():
        if pm.id != payment_method_id:
            stripe.PaymentMethod.detach(pm.id)


T = TypeVar("T")
MAX_TRIES = 10


def retry(f: Callable[[], T]) -> T:
    """Retries a stripe operation if it fails with a rate limit error."""
    its = 0
    while True:
        try:
            return f()
        except stripe.error.RateLimitError:
            its += 1
            if its > MAX_TRIES:
                raise
            # Retry.
            # Especially when starting a lot of parallel tests, we can get rate limit errors.
            time.sleep(1.0 * (1.0 + random.random()))
