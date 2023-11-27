from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from decimal import Decimal
import random
import time
from logging import getLogger
from typing import Any, Callable, Dict, List, TypeVar

from service.config import debug_mode
from service.error import InternalServerError
from service.db import db_session
from shop.models import Product, ProductCategory
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


@dataclass
class StripeRecurring:
    interval: str
    interval_count: int


def makeradmin_to_stripe_recurring(makeradmin_product: Product, price_type: PriceType) -> StripeRecurring | None:
    if price_type == PriceType.RECURRING or price_type == PriceType.BINDING_PERIOD:
        if makeradmin_product.unit in makeradmin_unit_to_stripe_unit:
            interval = makeradmin_unit_to_stripe_unit[makeradmin_product.unit]
        else:
            raise ValueError(f"Unexpected unit {makeradmin_product.unit} in makeradmin product {makeradmin_product.id}")
        interval_count = makeradmin_product.smallest_multiple if price_type == PriceType.BINDING_PERIOD else 1
        return StripeRecurring(interval=interval, interval_count=interval_count)
    else:
        return None


def get_stripe_product_id(makeradmin_product: Product) -> str:
    prefix = "debug" if debug_mode() else "prod"
    return f"{prefix}_{makeradmin_product.id}"


def get_stripe_price_lookup_key(makeradmin_product: Product, price_type: PriceType) -> str:
    prefix = "debug" if debug_mode() else "prod"
    return f"{prefix}_{makeradmin_product.id}_{price_type.value}"


def get_stripe_product(makeradmin_product: Product) -> stripe.Product | None:
    id = get_stripe_product_id(makeradmin_product)
    try:
        return retry(lambda: stripe.Product.retrieve(id=id))
    except stripe.error.InvalidRequestError as e:
        logger.warning(
            f"failed to retrive product from stripe for makeradmin product with id {makeradmin_product.id}, {e}"
        )
        return None


def get_stripe_prices(
    stripe_product: stripe.Product, lookup_keys: List[str] | None = None
) -> list[stripe.Price] | None:
    try:
        return list(retry(lambda: stripe.Price.list(product=stripe_product.stripe_id, lookup_keys=lookup_keys)))
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"failed to retrive prices from stripe for stripe product with id {stripe_product.id}, {e}")
        return None


def eq_makeradmin_stripe_product(makeradmin_product: Product, stripe_product: stripe.Product) -> bool:
    """Check that the essential parts of the product are the same in both makeradmin and stripe"""
    return stripe_product.name == makeradmin_product.name


def eq_makeradmin_stripe_price(makeradmin_product: Product, stripe_price: stripe.Price, price_type: PriceType) -> bool:
    """Check that the essential parts of the price are the same in both makeradmin and stripe"""
    recurring = makeradmin_to_stripe_recurring(makeradmin_product, price_type)
    different = []

    if recurring:
        if stripe_price.recurring is None:
            return False
        different.append(stripe_price.recurring.get("interval") != recurring.interval)
        different.append(stripe_price.recurring.get("interval_count") != recurring.interval_count)
    different.append(stripe_price.unit_amount != stripe_amount_from_makeradmin_product(makeradmin_product, recurring))
    different.append(stripe_price.currency != CURRENCY)
    different.append(stripe_price.metadata.get("price_type") != price_type.value)
    return not any(different)


def _create_stripe_product(makeradmin_product: Product) -> stripe.Product:
    id = get_stripe_product_id(makeradmin_product)
    stripe_product = retry(
        lambda: stripe.Product.create(
            id=id,
            name=makeradmin_product.name,
            description=f"Created by Makeradmin, product id (#{makeradmin_product.id})",
        )
    )
    return stripe_product


def _create_stripe_price(
    makeradmin_product: Product, stripe_product: stripe.Product, price_type: PriceType
) -> stripe.Price:
    key = get_stripe_price_lookup_key(makeradmin_product, price_type)
    recurring = makeradmin_to_stripe_recurring(makeradmin_product, price_type)
    recurring_dict = asdict(recurring) if recurring else {}
    stripe_price = retry(
        lambda: stripe.Price.create(
            lookup_key=key,
            nickname=key,
            transfer_lookup_key=True,
            product=stripe_product.id,
            unit_amount=stripe_amount_from_makeradmin_product(makeradmin_product, recurring),
            currency=CURRENCY,
            recurring=recurring_dict,
            metadata={"price_type": price_type.value},
        )
    )
    return stripe_price


def find_or_create_stripe_product(makeradmin_product: Product) -> stripe.Product:
    stripe_product = get_stripe_product(makeradmin_product)
    if stripe_product is None:
        stripe_product = _create_stripe_product(makeradmin_product)
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
    makeradmin_product: Product, stripe_product: stripe.Product
) -> Dict[PriceType, stripe.Price]:
    price_types = []
    if makeradmin_product.category.id != get_subscription_category().id:
        price_types.append(PriceType.FIXED_PRICE)
    else:
        price_types.append(PriceType.RECURRING)
        if makeradmin_product.smallest_multiple != 1:
            price_types.append(PriceType.BINDING_PERIOD)

    lookup_keys = [get_stripe_price_lookup_key(makeradmin_product, price_type) for price_type in price_types]
    stripe_prices = get_stripe_prices(stripe_product, lookup_keys=lookup_keys)

    prices_to_return: Dict[PriceType, stripe.Price | None] = {}
    if stripe_prices is None:
        prices_to_create = price_types
    else:
        prices_to_create = []
        for price_type in price_types:
            stripe_price = _find_price_type(stripe_prices, price_type)
            if stripe_price:
                prices_to_return[price_type] = stripe_price
            else:
                prices_to_create.append(price_type)

    for price_type in prices_to_create:
        prices_to_return[price_type] = _create_stripe_price(makeradmin_product, stripe_product, price_type)

    return prices_to_return


def update_stripe_product(makeradmin_product: Product, stripe_product: stripe.Product) -> stripe.Product:
    """Update the stripe product to match the makeradmin product"""
    return retry(lambda: stripe.Product.modify(stripe_product.id, name=makeradmin_product.name))


def replace_stripe_price(
    makeradmin_product: Product, stripe_price: stripe.Price, price_type: PriceType
) -> stripe.Price:
    """Create a new price based on the price etc in the makeradmin product to replace the old stripe price"""
    if get_stripe_product_id(makeradmin_product) != stripe_price.product:
        raise InternalServerError(
            f"The product for stripe price with id {stripe_price.id} does not match the product {makeradmin_product.id} in makeradmin."
        )
    if get_stripe_price_lookup_key(makeradmin_product, price_type) != stripe_price.lookup_key:
        raise InternalServerError(
            f"The lookup key for stripe price {stripe_price.id} does not match makeradmin product {makeradmin_product.id}"
        )
    deactivate_stripe_price(stripe_price)
    stripe_product = get_stripe_product(makeradmin_product)
    if stripe_product is None:
        raise RuntimeError(f"Failed to fetch stripe product for makeradmin product {makeradmin_product.id}")
    new_stripe_price = _create_stripe_price(makeradmin_product, stripe_product, price_type)
    if new_stripe_price is None:
        raise RuntimeError(f"Failed to replace price {stripe_price.id}")
    return new_stripe_price


def activate_stripe_product(stripe_product: stripe.Product) -> stripe.Product:
    return retry(lambda: stripe.Product.modify(stripe_product.id, active=True))


def deactivate_stripe_product(stripe_product: stripe.Product) -> stripe.Product:
    return retry(lambda: stripe.Product.modify(stripe_product.id, active=False))


def activate_stripe_price(stripe_price: stripe.Price) -> stripe.Price:
    return retry(lambda: stripe.Price.modify(stripe_price.id, active=True))


def deactivate_stripe_price(stripe_price: stripe.Price) -> stripe.Price:
    return retry(lambda: stripe.Price.modify(stripe_price.id, active=True))


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
