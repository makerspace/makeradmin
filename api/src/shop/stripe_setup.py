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
    SubscriptionScheduleStatus,
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
# TODO cache
def get_stripe_products() -> List[stripe.Product]:
    products = retry(lambda: stripe.Product.list())
    return products


# TODO only list with correct mode
# TODO cache?
def get_stripe_prices(stripe_product: stripe.Product):
    prices = list(retry(lambda: stripe.Price.list(product=stripe_product.stripe_id)))
    return prices


def check_difference_with_stripe(makeradmin_product: Product, stripe_products:List[stripe.Product]):
    # find the corresponding product
    for p in stripe_products:
        if makeradmin_product.get_metadata(MSMetaKeys.SPECIAL_PRODUCT_ID) == p.metadata[MSMetaKeys.SPECIAL_PRODUCT_ID]
            stripe_product = p
            break
    # prices = get_stripe_prices(stripe_product)

    # diff
    # active
    # binding period
    # period

    # price stuff
    # price
    # currency

    # check that
    # is subscription


def update_stripe_product(makeradmin_product: Product, difference):
    pass
    # loop over the dict and update stuff


def setup_stripe_discounts():
    # TODO check if the keys are set or not
    logger.info("setting up stripe discounts")
    # TODO


def setup_stripe_products():
    # TODO check if the keys are set or not
    logger.info("setting up stripe products")
    stripe_products = get_stripe_products()

    makeradmin_category = get_category()
    makeradmin_products = db_session.query(Product).filter(ProductCategory.id == makeradmin_category.id)
    # TODO probably print a warning about the stuff we expect are in the makeradmin products?
    for makeradmin_product in makeradmin_products:
        setup_stripe_product(makeradmin_product, stripe_products)


def setup_stripe_product(makeradmin_product: Product, stripe_products: List[stripe.Product] = None):
    # TODO check if the keys are set or not
    if stripe_products is None:
        stripe_products = get_stripe_products()
    difference = check_difference_with_stripe(makeradmin_product, stripe_products)
    if difference:
        update_stripe_product(makeradmin_product, difference)


def setup_stripe(dev_mode: bool):
    # TODO check if the keys are set or not
    # TODO use dev_mode bool

    logger.info("setting up stripe")
    stripe.api_version = "2022-11-15"
    set_stripe_key(private=True)  # TODO based on mode?

    setup_stripe_products()
    setup_stripe_discounts()
