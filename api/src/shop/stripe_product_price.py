from dataclasses import asdict, dataclass
from logging import getLogger
from typing import Any, Dict, List, Tuple

import stripe
from service.db import db_session
from service.error import InternalServerError

from shop.models import Product
from shop.stripe_constants import (
    CURRENCY,
    MakerspaceMetadataKeys,
    PriceType,
)
from shop.stripe_util import StripeRecurring, get_subscription_category, retry, stripe_amount_from_makeradmin_product

logger = getLogger("makeradmin")

makeradmin_unit_to_stripe_unit = {
    "mån": "month",
    "month": "month",
    "år": "year",
    "year": "year",
}


def makeradmin_to_stripe_recurring(makeradmin_product: Product, price_type: PriceType) -> StripeRecurring | None:
    subscription_category_id = get_subscription_category().id
    if price_type == PriceType.RECURRING or price_type == PriceType.BINDING_PERIOD:
        if makeradmin_product.category.id != subscription_category_id:
            raise ValueError(f"Unexpected price type {price_type} for non-subscription product {makeradmin_product.id}")
        if makeradmin_product.unit in makeradmin_unit_to_stripe_unit:
            interval = makeradmin_unit_to_stripe_unit[makeradmin_product.unit]
        else:
            raise ValueError(f"Unexpected unit {makeradmin_product.unit} in makeradmin product {makeradmin_product.id}")
        interval_count = makeradmin_product.smallest_multiple if price_type == PriceType.BINDING_PERIOD else 1
        return StripeRecurring(interval=interval, interval_count=interval_count)
    else:
        if makeradmin_product.category.id == subscription_category_id:
            raise ValueError(f"Unexpected price type {price_type} for subscription product {makeradmin_product.id}")
        return None


def get_stripe_price_lookup_key(makeradmin_product: Product, price_type: PriceType) -> str:
    if makeradmin_product.stripe_product_id is None:
        raise InternalServerError(
            f"No stripe product id found for makeradmin product with id {makeradmin_product.id}."
            + f" This product likely does not have a corresponding stripe product."
        )
    return f"{makeradmin_product.stripe_product_id}_{price_type.value}"


def get_stripe_product(makeradmin_product: Product) -> stripe.Product | None:
    stripe_id = makeradmin_product.stripe_product_id
    if stripe_id is None:
        return None
    try:
        return retry(lambda: stripe.Product.retrieve(id=stripe_id))
    except stripe.InvalidRequestError as e:
        logger.warning(
            f"failed to retrive product from stripe for makeradmin product with"
            + f" makeradmin id {makeradmin_product.id} and stripe product id {stripe_id}, {e}"
        )
        return None


def get_stripe_prices(
    stripe_product: stripe.Product, lookup_keys: List[str] | None = None
) -> list[stripe.Price] | None:
    try:
        return list(retry(lambda: stripe.Price.list(product=stripe_product.id, lookup_keys=lookup_keys)))
    except stripe.InvalidRequestError as e:
        logger.warning(f"failed to retrive prices from stripe for stripe product with id {stripe_product.id}, {e}")
        return None


def eq_makeradmin_stripe_product(makeradmin_product: Product, stripe_product: stripe.Product) -> bool:
    """Check that the essential parts of the product are the same in both makeradmin and stripe"""
    if stripe_product.id != makeradmin_product.stripe_product_id:
        raise ValueError(
            f"Stripe product id {stripe_product.id} and the stripe id, {makeradmin_product.stripe_product_id}, "
            + f"associated with makeradmin product id {makeradmin_product.id} does not match"
        )
    return stripe_product.name == makeradmin_product.name


def eq_makeradmin_stripe_price(makeradmin_product: Product, stripe_price: stripe.Price, price_type: PriceType) -> bool:
    """Check that the essential parts of the price are the same in both makeradmin and stripe"""
    lookup_key_for_product = get_stripe_price_lookup_key(makeradmin_product, price_type)
    if stripe_price.lookup_key != lookup_key_for_product:
        raise ValueError(
            f"Stripe price lookup key {stripe_price.lookup_key} and corresponding key from"
            + f" makeradmin product {makeradmin_product.id} and PriceType {price_type} does not match"
        )

    recurring = makeradmin_to_stripe_recurring(makeradmin_product, price_type)

    if (
        stripe_price.unit_amount != stripe_amount_from_makeradmin_product(makeradmin_product, recurring)
        or stripe_price.currency != CURRENCY
        or stripe_price.metadata.get("price_type") != price_type.value
    ):
        return False

    # Check that either both are recurring, or none are recurring
    if (recurring is not None) != (stripe_price.recurring is not None):
        return False

    if recurring is not None:
        return (
            stripe_price.recurring.get("interval") == recurring.interval
            and stripe_price.recurring.get("interval_count") == recurring.interval_count
        )

    return True


def _create_stripe_product(makeradmin_product: Product) -> stripe.Product:
    stripe_product = retry(
        lambda: stripe.Product.create(
            name=makeradmin_product.name,
            description=f"Created by Makeradmin, product id (#{makeradmin_product.id})",
            metadata={
                MakerspaceMetadataKeys.PRODUCT_ID.value: makeradmin_product.id,
            },
        )
    )
    makeradmin_product.stripe_product_id = stripe_product.id
    db_session.flush()
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
            metadata={
                MakerspaceMetadataKeys.PRICE_TYPE.value: price_type.value,
                MakerspaceMetadataKeys.PRODUCT_ID.value: makeradmin_product.id,
            },
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
            if stripe_price is not None:
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
    if makeradmin_product.stripe_product_id != stripe_price.product:
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
