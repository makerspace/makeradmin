from logging import getLogger
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast
from sqlalchemy import func


import stripe
from test_aid.systest_config import STRIPE_PRIVATE_KEY, STRIPE_PUBLIC_KEY

from shop.models import Product, ProductCategory
from shop.stripe_constants import (
    PriceType,
)
from shop.stripe_util import retry
from service.config import config
from service.db import db_session
from service.error import InternalServerError

logger = getLogger("makeradmin")


def set_stripe_key(private: bool) -> None:
    stripe.api_key = STRIPE_PRIVATE_KEY if private else STRIPE_PUBLIC_KEY


def setup_stripe_products(livemode: bool) -> None:
    mode_str = "production" if livemode else "test/dev"
    logger.info(f"setting up stripe products with mode {mode_str}")

    subscription_category = get_subscription_category()
    makeradmin_products = db_session.query(Product).filter(ProductCategory.id == subscription_category.id)
    for makeradmin_product in makeradmin_products:
        setup_stripe_product_and_prices(makeradmin_product, livemode)


def setup_stripe_product_and_prices(makeradmin_product: Product, livemode: bool) -> None:
    stripe_product = find_or_create_stripe_product(makeradmin_product, livemode)
    if stripe_product is None:
        raise InternalServerError(f"Failed to find/create stripe product for makeradmin product {makeradmin_product}")

    if not eq_makeradmin_stripe_product(makeradmin_product, stripe_product):
        update_stripe_product(makeradmin_product, stripe_product)

    stripe_prices = find_or_create_stripe_prices_for_product(makeradmin_product, stripe_product, livemode)
    for price_type, stripe_price in stripe_prices.items():
        if stripe_price is None:
            raise InternalServerError(
                f"Failed to find/create stripe price for makeradmin product {makeradmin_product} with price type {price_type}"
            )

        if not eq_makeradmin_stripe_price(makeradmin_product, stripe_price, price_type):
            stripe_price = replace_stripe_price(makeradmin_product, stripe_price, price_type, livemode)
        if not stripe_price.active:
            stripe_price = activate_stripe_price(stripe_price)
    if not stripe_product.active:
        stripe_product = activate_stripe_product(stripe_product)


def setup_stripe(livemode: bool) -> None:
    mode_str = "production" if livemode else "test/dev"
    logger.info(f"setting up stripe in {mode_str} mode")
    stripe.api_version = "2022-11-15"
    set_stripe_key(private=True)

    if stripe.api_key is None:
        logger.warning("skipping setting up stripe, keys are not set")
        return

    setup_stripe_products(livemode)
