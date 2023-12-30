from logging import getLogger

import stripe
from service.config import debug_mode
from service.db import db_session
from test_aid.systest_config import STRIPE_PRIVATE_KEY, STRIPE_PUBLIC_KEY

from shop.models import Product, ProductCategory
from shop.stripe_util import get_and_sync_stripe_product_and_prices, get_subscription_category

logger = getLogger("makeradmin")


def set_stripe_key(private: bool) -> None:
    stripe.api_key = STRIPE_PRIVATE_KEY if private else STRIPE_PUBLIC_KEY


def setup_stripe_products() -> None:
    mode_str = "debug" if debug_mode() else "production"
    logger.info(f"setting up stripe products with mode {mode_str}")

    subscription_category = get_subscription_category()
    makeradmin_products = db_session.query(Product).filter(ProductCategory.id == subscription_category.id)
    for makeradmin_product in makeradmin_products:
        get_and_sync_stripe_product_and_prices(makeradmin_product)


def setup_stripe() -> None:
    mode_str = "debug" if debug_mode() else "production"
    logger.info(f"setting up stripe in {mode_str} mode")
    stripe.api_version = "2022-11-15"
    set_stripe_key(private=True)

    if stripe.api_key is None:
        logger.warning("skipping setting up stripe, keys are not set")
        return

    setup_stripe_products()
