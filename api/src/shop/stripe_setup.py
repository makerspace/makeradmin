from logging import getLogger

import stripe
from service.config import debug_mode
from service.db import db_session
from test_aid.systest_config import STRIPE_PRIVATE_KEY, STRIPE_PUBLIC_KEY

from shop.models import Product, ProductCategory
from shop.stripe_product_price import get_and_sync_stripe_product_and_prices
from shop.stripe_util import get_subscription_category

logger = getLogger("makeradmin")


def set_stripe_key(private: bool) -> None:
    stripe.api_key = STRIPE_PRIVATE_KEY if private else STRIPE_PUBLIC_KEY


def are_stripe_keys_set() -> bool:
    return bool(STRIPE_PRIVATE_KEY and STRIPE_PUBLIC_KEY)


def are_stripe_keys_live() -> bool:
    if "live" in STRIPE_PRIVATE_KEY and "live" in STRIPE_PUBLIC_KEY:
        return True
    elif "test" in STRIPE_PRIVATE_KEY and "test" in STRIPE_PUBLIC_KEY:
        return False
    else:
        raise Exception(
            "Stripe keys in .env must both be set to either 'live' or 'test'. Please check your configuration."
        )


def setup_stripe_products() -> None:
    logger.info(f"setting up stripe products")
    subscription_category = get_subscription_category()
    makeradmin_products = db_session.query(Product).filter(Product.category_id == subscription_category.id)
    for makeradmin_product in makeradmin_products:
        get_and_sync_stripe_product_and_prices(makeradmin_product)


def setup_stripe(private: bool) -> None:
    logger.info(f"setting up stripe")
    stripe.api_version = "2024-06-20"
    set_stripe_key(private=private)
