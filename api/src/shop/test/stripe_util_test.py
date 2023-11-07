from datetime import datetime, timezone
from logging import getLogger
from unittest import skipIf

import membership.models
import shop.models
import messages.models
import core.models
from shop import stripe_util
from shop.models import Product, ProductAction
from shop.stripe_constants import (
    STRIPE_CURRENTY_BASE,
    PriceType,
    CURRENCY,
)
import stripe
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class Test(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]
    products = [
        dict(
            name="test månad enkel",
            price=100.0,
            id=1000,
            unit="mån",
            smallest_multiple=1,
        ),
        dict(
            name="test år enkel",
            price=200.0,
            id=10001,
            unit="år",
            smallest_multiple=1,
        ),
        dict(
            name="test månad med bindingstid",
            price=300.0,
            id=10002,
            unit="månad",
            smallest_multiple=2,
        ),
    ]

    @skipIf(not stripe.api_key, "stripe util tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_products = []

    def tearDown(self) -> None:
        # It is not possible to delete prices through the api so we set them as inactive instead
        for makeradmin_product in self.seen_products:
            stripe_product = stripe_util.get_stripe_product(makeradmin_product, livemode=False)
            if stripe_product is None:
                continue
            stripe_prices = stripe_util.get_stripe_prices(stripe_product, livemode=False)
            if stripe_prices is None:
                continue
            for price in stripe_prices:
                stripe_util.retry(lambda: stripe.Product.modify(price.id, active=False))
            stripe_util.retry(lambda: stripe.Product.modify(stripe_product.id, active=False))
            return super().tearDown()

    def test_create_product(self) -> None:
        makeradmin_test_product = self.products[0]
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product, livemode=False)
        assert stripe_test_product.name == makeradmin_test_product["name"]
