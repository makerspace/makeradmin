from dataclasses import asdict, dataclass
from logging import getLogger
from typing import Any, Callable, Dict, List, Tuple, TypeVar

from service.config import debug_mode
from service.error import InternalServerError
from shop.models import Product
from shop.stripe_constants import (
    PriceType,
    CURRENCY,
)
from shop.stripe_util import StripeRecurring, retry, stripe_amount_from_makeradmin_product, get_subscription_category
import stripe

logger = getLogger("makeradmin")

makeradmin_unit_to_stripe_unit = {
    "mån": "month",
    "month": "month",
    "år": "year",
    "year": "year",
}


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


def get_or_create_stripe_product(makeradmin_product: Product) -> stripe.Product:
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


def get_or_create_stripe_prices_for_product(
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


def get_and_sync_stripe_product(makeradmin_product: Product) -> stripe.Product:
    try:
        stripe_product = get_or_create_stripe_product(makeradmin_product)
        if not eq_makeradmin_stripe_product(makeradmin_product, stripe_product):
            stripe_product = update_stripe_product(makeradmin_product, stripe_product)
        if not stripe_product.active:
            stripe_product = activate_stripe_product(stripe_product)
        return stripe_product
    except Exception as e:
        raise InternalServerError(
            f"Failed to sync stripe product for makeradmin product {makeradmin_product}. Exception {e}"
        )


def get_and_sync_stripe_prices_for_product(
    makeradmin_product: Product, stripe_product: stripe.Product
) -> Dict[PriceType, stripe.Price]:
    try:
        stripe_prices = get_or_create_stripe_prices_for_product(makeradmin_product, stripe_product)
        for price_type, stripe_price in stripe_prices.items():
            if not eq_makeradmin_stripe_price(makeradmin_product, stripe_price, price_type):
                stripe_prices[price_type] = replace_stripe_price(makeradmin_product, stripe_price, price_type)
            if not stripe_price.active:
                stripe_prices[price_type] = activate_stripe_price(stripe_price)
        return stripe_prices
    except Exception as e:
        raise InternalServerError(
            f"Failed to sync stripe prices for makeradmin product {makeradmin_product}. Exception {e}"
        )


def get_and_sync_stripe_product_and_prices(
    makeradmin_product: Product,
) -> Tuple[stripe.Product, Dict[PriceType, stripe.Price]]:
    stripe_product = get_and_sync_stripe_product(makeradmin_product)
    stripe_prices = get_and_sync_stripe_prices_for_product(makeradmin_product, stripe_product)
    return (stripe_product, stripe_prices)


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
