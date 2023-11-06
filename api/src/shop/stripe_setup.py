from logging import getLogger
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast
from sqlalchemy import func


import stripe
from test_aid.systest_config import STRIPE_PRIVATE_KEY, STRIPE_PUBLIC_KEY

from shop.models import Product, ProductAction, ProductCategory
from shop.stripe_constants import (
    STRIPE_CURRENTY_BASE,
    MakerspaceMetadataKeys as MSMetaKeys,
    PriceType,
    CURRENCY,
)
from shop.stripe_util import retry
from service.config import config
from service.db import db_session

logger = getLogger("makeradmin")


def set_stripe_key(private: bool) -> None:
    stripe.api_key = STRIPE_PRIVATE_KEY if private else STRIPE_PUBLIC_KEY


def get_category() -> ProductCategory:
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


# TODO only list with correct mode
# TODO cache?
def get_stripe_product(makeradmin_product: Product) -> stripe.Product | None:
    try:
        product = retry(lambda: stripe.Product.retrieve(str(makeradmin_product.id)))
    except stripe.error.InvalidRequestError as e:
        logger.warning(
            f"failed to retrive product from stripe for makeradmin product with id {makeradmin_product.id}, {e}"
        )
        return None
    return product


# TODO only list with correct mode
# TODO cache?
def get_stripe_prices(stripe_product: stripe.Product):
    try:
        prices = list(retry(lambda: stripe.Price.list(product=stripe_product.stripe_id)))
    except stripe.error.InvalidRequestError as e:
        logger.warning(f"failed to retrive prices from stripe for stripe product with id {stripe_product.id}, {e}")
        return None
    return prices


def check_stripe_prices(stripe_prices: list[stripe.Price]):
    differences = [[]] * len(stripe_prices)
    # TODO deal with the multple prices case
    for i, price in enumerate(stripe_prices):
        if not price.active:
            differences[i].append("active")
        if price.currency != CURRENCY:
            differences[i].append("currency")
    return differences
    # TODO check
    # recuring interval and count
    # price
    # currency


def check_stripe_product(makeradmin_product: Product, stripe_product: stripe.Product):
    differences = []
    if not stripe_product.active:
        differences.append("active")
    if stripe_product.name != makeradmin_product.name:
        differences.append("name")
    return differences


def create_stripe_product(makeradmin_product: Product) -> stripe.Product | None:
    stripe_product = retry(
        lambda: stripe.Product.create(
            id=str(makeradmin_product.id),
            name=makeradmin_product.name,
            description=f"Created by Makeradmin, product id (#{makeradmin_product.id})",
        )
    )
    return stripe_product


def _create_stripe_price(makeradmin_product: Product, stripe_product: stripe.Product, priceType: PriceType):
    interval = "month"  # TODO how to control this? use the unit?
    interval_count = makeradmin_product.smallest_multiple
    recurring = {"interval": interval, "interval_count": interval_count}
    stripe_price = retry(
        lambda: stripe.Price.create(
            name=f"{makeradmin_product.name} price {priceType}",
            product=stripe_product.id,
            description=f"Created by Makeradmin (#{makeradmin_product.id})",
            unit_amount=makeradmin_product.price * interval_count,
            currency=CURRENCY,
            recurring=recurring,
            metadata={"priceType": priceType},
        )
    )
    return stripe_price


def create_stripe_prices_for_product(
    makeradmin_product: Product, stripe_product: stripe.Product
) -> stripe.Price | None:
    interval_count = makeradmin_product.smallest_multiple

    stripe_prices = [_create_stripe_price(makeradmin_product, stripe_product)]
    if interval_count > 1:
        stripe_prices.append(_create_stripe_price())
    return stripe_prices


def update_stripe_prices_for_product(makeradmin_product: Product, stripe_prices: list[stripe.Price], difference):
    # TODO
    pass
    # loop over the things to update and update stuff


def update_stripe_product(makeradmin_product: Product, difference):
    # TODO
    pass
    # loop over the things to update and update stuff


def setup_stripe_discounts():
    # TODO check if the stripe keys are set or not
    logger.info("setting up stripe discounts")
    # TODO


def setup_stripe_products():
    # TODO check if the stripe keys are set or not
    logger.info("setting up stripe products")

    makeradmin_category = get_category()
    makeradmin_products = db_session.query(Product).filter(ProductCategory.id == makeradmin_category.id)
    # TODO assert that the correct products are in the makeradmin db
    for makeradmin_product in makeradmin_products:
        setup_stripe_product(makeradmin_product)


def setup_stripe_product(makeradmin_product: Product):
    # TODO check if the stripe keys are set or not
    stripe_product = get_stripe_product(makeradmin_product)
    if stripe_product is None:
        stripe_product = create_stripe_product(makeradmin_product)
        create_stripe_prices_for_product(makeradmin_product, stripe_product)
        # TODO error handling
        return

    product_difference = check_stripe_product(makeradmin_product, stripe_product)
    if product_difference:
        update_stripe_product(makeradmin_product, product_difference)

    stripe_prices = get_stripe_prices(stripe_product)
    if stripe_prices is None:
        create_stripe_prices_for_product(makeradmin_product, stripe_product)
        # TODO error handling
        return

    price_difference = check_stripe_prices(stripe_prices)
    if price_difference:
        update_stripe_prices_for_product(makeradmin_product, stripe_prices, price_difference)


def setup_stripe(dev_mode: bool):
    # TODO check if the stripe keys are set or not
    # TODO use dev_mode bool

    logger.info("setting up stripe")
    stripe.api_version = "2022-11-15"
    set_stripe_key(private=True)  # TODO based on mode?

    setup_stripe_products()
    setup_stripe_discounts()
