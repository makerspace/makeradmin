from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import random
import time
from logging import getLogger
from typing import Any, Callable, Dict, TypeVar

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


class StripeDifference(Enum):
    Equal = "equal"
    DifferentChangable = "different chanagable"
    DifferentUnchangable = "different unchangable"


def makeradmin_to_stripe_recurring(makeradmin_product: Product, price_type: PriceType) -> Dict[str, Any]:
    if price_type == PriceType.RECURRING or price_type == PriceType.BINDING_PERIOD:
        if makeradmin_product.unit in makeradmin_unit_to_stripe_unit:
            interval = makeradmin_unit_to_stripe_unit[makeradmin_product.unit]
        else:
            raise ValueError(f"Unexpected unit {makeradmin_product.unit} in makeradmin product {makeradmin_product.id}")
        interval_count = makeradmin_product.smallest_multiple if price_type == PriceType.BINDING_PERIOD else 1
        return {"interval": interval, "interval_count": interval_count}
    else:
        return {}


def get_stripe_product_id(makeradmin_product: Product, livemode: bool = False) -> str:
    return f"prod_{makeradmin_product.id}" if livemode else f"test_{makeradmin_product.id}"


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


def get_stripe_prices(
    stripe_product: stripe.Product, filter_inactive: bool = True, livemode: bool = False
) -> list[stripe.Price] | None:
    try:
        prices = list(retry(lambda: stripe.Price.list(product=stripe_product.stripe_id)))
        if filter_inactive:
            prices = [p for p in prices if p.active]
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"failed to retrive prices from stripe for stripe product with id {stripe_product.id}, {e}")
        return None
    for p in prices:
        assert p.livemode == livemode
    return prices


def eq_makeradmin_stripe_product(makeradmin_product: Product, stripe_product: stripe.Product) -> StripeDifference:
    if stripe_product.name == makeradmin_product.name:
        return StripeDifference.Equal
    else:
        return StripeDifference.DifferentChangable


def eq_makeradmin_stripe_price(
    makeradmin_product: Product, stripe_price: stripe.Price, price_type: PriceType
) -> StripeDifference:
    recurring = makeradmin_to_stripe_recurring(makeradmin_product, price_type)
    different_changable = []
    different_unchangable = []

    if len(recurring) != 0:
        if stripe_price.recurring is None:
            return StripeDifference.DifferentUnchangable
        different_unchangable.append(stripe_price.recurring.get("interval") != recurring["interval"])
        different_unchangable.append(stripe_price.recurring.get("interval_count") != recurring["interval_count"])
    different_changable.append(
        stripe_price.unit_amount != stripe_amount_from_makeradmin_product(makeradmin_product, recurring)
    )
    different_changable.append(stripe_price.currency != CURRENCY)
    different_changable.append(stripe_price.metadata.get("price_type") != price_type.value)

    if any(different_unchangable):
        return StripeDifference.DifferentUnchangable
    if any(different_changable):
        return StripeDifference.DifferentChangable
    return StripeDifference.Equal


def eq_makeradmin_stripe(
    makeradmin_product: Product, stripe_product: stripe.Product, stripe_prices: Dict[PriceType, stripe.Price]
) -> Dict[str, StripeDifference]:
    differences = {"product": eq_makeradmin_stripe_product(makeradmin_product, stripe_product)}
    interval_count = makeradmin_product.smallest_multiple
    expected_number_of_prices = 1 if interval_count == 1 else 2
    if len(stripe_prices) != expected_number_of_prices:
        raise RuntimeError(
            f"Number of stripe prices does not match with makeradmin product multiplier. Got {len(stripe_prices)}, expected {expected_number_of_prices}"
        )
    differences[PriceType.RECURRING.value] = eq_makeradmin_stripe_price(
        makeradmin_product, stripe_prices[PriceType.RECURRING], PriceType.RECURRING
    )
    if expected_number_of_prices == 2:
        differences[PriceType.BINDING_PERIOD.value] = eq_makeradmin_stripe_price(
            makeradmin_product, stripe_prices[PriceType.BINDING_PERIOD], PriceType.BINDING_PERIOD
        )
    return differences


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
    makeradmin_product: Product, stripe_product: stripe.Product, price_type: PriceType, livemode: bool = False
) -> stripe.Price | None:
    nickname = (
        f"prod_{makeradmin_product.id}_{price_type.value}"
        if livemode
        else f"test_{makeradmin_product.id}_{price_type.value}"
    )
    recurring = makeradmin_to_stripe_recurring(makeradmin_product, price_type)
    stripe_price = retry(
        lambda: stripe.Price.create(
            nickname=nickname,
            product=stripe_product.id,
            unit_amount=stripe_amount_from_makeradmin_product(makeradmin_product, recurring),
            currency=CURRENCY,
            recurring=recurring,
            metadata={"price_type": price_type.value},
        )
    )
    assert stripe_price.livemode == livemode
    return stripe_price


def find_or_create_stripe_product(makeradmin_product: Product, livemode: bool = False) -> stripe.Product | None:
    stripe_product = get_stripe_product(makeradmin_product, livemode)
    if stripe_product is None:
        stripe_product = _create_stripe_product(makeradmin_product, livemode)
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
) -> Dict[PriceType, stripe.Price] | None:
    interval_count = makeradmin_product.smallest_multiple
    stripe_prices = get_stripe_prices(stripe_product, filter_inactive=False, livemode=livemode)

    stripe_price_recurring = _find_price_type(stripe_prices, PriceType.RECURRING)

    if stripe_price_recurring is None:
        stripe_price_recurring = _create_stripe_price(makeradmin_product, stripe_product, PriceType.RECURRING, livemode)
    if interval_count == 1:
        return {PriceType.RECURRING: stripe_price_recurring}

    stripe_price_binding = _find_price_type(stripe_prices, PriceType.BINDING_PERIOD)
    if stripe_price_binding is None:
        stripe_price_binding = _create_stripe_price(
            makeradmin_product, stripe_product, PriceType.BINDING_PERIOD, livemode
        )
    return {PriceType.RECURRING: stripe_price_recurring, PriceType.BINDING_PERIOD: stripe_price_binding}


def update_stripe_product(makeradmin_product: Product, stripe_product: stripe.Product) -> stripe.Product:
    """Update the stripe product to match the makeradmin product, i.e. change it's name."""
    return retry(lambda: stripe.Product.modify(stripe_product.id, name=makeradmin_product.name))


# TODO this is broken
def update_stripe_price(makeradmin_product: Product, stripe_price: stripe.Price, price_type: PriceType) -> stripe.Price:
    """Update the stripe price to match the makeradmin product and price type.
    It is not possible to update interval and interval_count"""
    recurring = makeradmin_to_stripe_recurring(makeradmin_product, price_type)
    if stripe_price.recurring or len(recurring) != 0:
        if (
            recurring["interval"] != stripe_price.recurring["interval"]
            or recurring["interval_count"] != stripe_price.recurring["interval_count"]
        ):
            raise ValueError(
                f"It is not possible to update the recurring part of a price, create a new one instead. Tried to update {stripe_price.recurring} to {recurring}"
            )
    unit_amount = stripe_amount_from_makeradmin_product(makeradmin_product, recurring)
    currency_options_param = {"unit_amount": unit_amount}
    currency_options = {CURRENCY: currency_options_param}
    return retry(
        lambda: stripe.Price.modify(
            stripe_price.id,
            currency_options=currency_options,
            metadata={"price_type": price_type.value},
        )
    )


def activate_stripe_product(stripe_product: stripe.Product) -> stripe.Product:
    return retry(lambda: stripe.Product.modify(stripe_product.id, active=True))


def deactivate_stripe_product(stripe_product: stripe.Product) -> stripe.Product:
    return retry(lambda: stripe.Product.modify(stripe_product.id, active=False))


def activate_stripe_price(stripe_price: stripe.Price) -> stripe.Price:
    return retry(lambda: stripe.Price.modify(stripe_price.id, active=True))


def deactivate_stripe_price(stripe_price: stripe.Price) -> stripe.Price:
    return retry(lambda: stripe.Price.modify(stripe_price.id, active=True))


def stripe_amount_from_makeradmin_product(makeradmin_product: Product, recurring: Dict[str, Any]) -> int:
    return convert_to_stripe_amount(makeradmin_product.price * recurring["interval_count"])


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
