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

makeradmin_unit_to_stripe_unit = {
    "mån": "month",
    "month": "month",
    "år": "year",
    "year": "year",
}


def get_stripe_product_id(makeradmin_product: Product, livemode: bool = False) -> str:
    return f"prod_{makeradmin_product.id}" if livemode else f"test_{makeradmin_product.id}"


# TODO cache?
def get_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    id = get_stripe_product_id(makeradmin_product, livemode)
    try:
        product = retry(lambda: stripe.Product.retrieve(id=id))
    except stripe.error.InvalidRequestError as e:
        logger.warning(
            f"failed to retrive product from stripe for makeradmin product with id {makeradmin_product.id}, {e}"
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
            prices = [p for p in prices if p.active]
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"failed to retrive prices from stripe for stripe product with id {stripe_product.id}, {e}")
        return None
    for p in prices:
        assert p.livemode == livemode
    return prices


def _create_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    id = get_stripe_product_id(makeradmin_product, livemode)
    stripe_product = retry(
        lambda: stripe.Product.create(
            id=id,
            name=makeradmin_product.name,
            description=f"Created by Makeradmin, product id (#{makeradmin_product.id})",
        )
    )
    assert stripe_product.livemode == livemode
    return stripe_product


def _create_stripe_price(
    makeradmin_product: Product, stripe_product: stripe.Product, priceType: PriceType, livemode: bool = False
) -> stripe.Price | None:
    nickname = (
        f"prod_{makeradmin_product.id}_{priceType.value}"
        if livemode
        else f"test_{makeradmin_product.id}_{priceType.value}"
    )
    if priceType == PriceType.RECURRING or priceType == PriceType.BINDING_PERIOD:
        if makeradmin_product.unit in makeradmin_unit_to_stripe_unit:
            interval = makeradmin_unit_to_stripe_unit[makeradmin_product.unit]
        else:
            raise RuntimeError(
                f"Unexpected unit {makeradmin_product.unit} in makeradmin product {makeradmin_product.id}"
            )
        interval_count = makeradmin_product.smallest_multiple if priceType == PriceType.BINDING_PERIOD else 1
        recurring = {"interval": interval, "interval_count": interval_count}
    else:
        interval_count = 1
        recurring = {}
    stripe_price = retry(
        lambda: stripe.Price.create(
            nickname=nickname,
            product=stripe_product.id,
            unit_amount=convert_to_stripe_amount(makeradmin_product.price * interval_count),
            currency=CURRENCY,
            recurring=recurring,
            metadata={"price_type": priceType.value},
        )
    )
    assert stripe_price.livemode == livemode
    return stripe_price


def find_or_create_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    stripe_product = get_stripe_product(makeradmin_product, livemode)
    if stripe_product is None:
        stripe_product = _create_stripe_product(makeradmin_product, livemode)
    elif not stripe_product.active:
        stripe_product = retry(lambda: stripe.Product.modify(stripe_product.id, active=True))
    return stripe_product


def _find_price_type(stripe_prices: list[stripe.Price] | None, price_type: PriceType) -> stripe.Price | None:
    if stripe_prices is None:
        return None
    for p in stripe_prices:
        metadata = p.metadata
        if metadata is None:
            continue
        if metadata["price_type"] == price_type.value:
            return p
    return None


def find_or_create_stripe_prices_for_product(
    makeradmin_product: Product, stripe_product: stripe.Product, livemode: bool = False
) -> list[stripe.Price] | None:
    interval_count = makeradmin_product.smallest_multiple
    stripe_prices = get_stripe_prices(stripe_product, filterInactive=False, livemode=livemode)

    stripe_price_recurring = _find_price_type(stripe_prices, PriceType.RECURRING)

    if stripe_price_recurring is None:
        stripe_price_recurring = _create_stripe_price(makeradmin_product, stripe_product, PriceType.RECURRING, livemode)
    elif not stripe_price_recurring.active:
        stripe_price_recurring = retry(lambda: stripe.Price.modify(stripe_price_recurring.id, active=True))

    if interval_count == 1:
        return [stripe_price_recurring]

    stripe_price_binding = _find_price_type(stripe_prices, PriceType.BINDING_PERIOD)
    if stripe_price_binding is None:
        stripe_price_binding = _create_stripe_price(
            makeradmin_product, stripe_product, PriceType.BINDING_PERIOD, livemode
        )
    elif not stripe_price_binding.active:
        stripe_price_binding = retry(lambda: stripe.Price.modify(stripe_price_binding.id, active=True))

    return [stripe_price_recurring, stripe_price_binding]


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
