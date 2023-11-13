from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import membership.models
import shop.models
import messages.models
import core.models
from shop import stripe_util
from shop.models import Product
from shop import stripe_constants
import stripe
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class StripeUtilWithoutStripeTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    def test_makeradmin_to_stripe_recurring_recurring(self) -> None:
        makeradmin_test_product = self.db.create_product(
            unit="mån",
            smallest_multiple=3,
        )
        recurring = stripe_util.makeradmin_to_stripe_recurring(
            makeradmin_test_product, stripe_constants.PriceType.RECURRING
        )
        assert recurring["interval"] == "month"
        assert recurring["interval_count"] == 1

    def test_makeradmin_to_stripe_recurring_binding(self) -> None:
        makeradmin_test_product = self.db.create_product(
            unit="mån",
            smallest_multiple=3,
        )
        recurring = stripe_util.makeradmin_to_stripe_recurring(
            makeradmin_test_product, stripe_constants.PriceType.BINDING_PERIOD
        )
        assert recurring["interval"] == "month"
        assert recurring["interval_count"] == 3

    def test_makeradmin_to_stripe_recurring_wrong_unit(self) -> None:
        makeradmin_test_product = self.db.create_product(
            unit="st",
        )
        with self.assertRaises(ValueError) as context:
            stripe_util.makeradmin_to_stripe_recurring(makeradmin_test_product, stripe_constants.PriceType.RECURRING),
        self.assertTrue("Unexpected unit" in str(context.exception))

    def test_stripe_amount_from_makeradmin_product(self) -> None:
        price = 200
        multiples = [1, 3]

        makeradmin_test_product = self.db.create_product(
            name="test",
            price=price,
            unit="mån",
            smallest_multiple=5,
        )
        for multiple in multiples:
            recurring = {"interval": "month", "interval_count": multiple}
            stripe_amount = stripe_util.stripe_amount_from_makeradmin_product(makeradmin_test_product, recurring)
            assert stripe_amount == multiple * price * stripe_constants.STRIPE_CURRENTY_BASE


class StripeUtilWithStripeTest(ShopTestMixin, FlaskTestBase):
    # The products id in makeradmin have to be unique in each test to prevent race conditions

    models = [membership.models, messages.models, shop.models, core.models]
    stripe_id_base = 4000

    @skipIf(not stripe.api_key, "stripe util tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_products: List[Product] = []

    @staticmethod
    def assertPrice(stripe_price: stripe.Price, makeradmin_product: Product) -> None:
        assert stripe_price.currency == stripe_constants.CURRENCY
        assert stripe_price.type == "recurring"
        reccuring = stripe_price.recurring
        if "mån" in makeradmin_product.unit:
            assert reccuring["interval"] == "month"
        else:
            assert reccuring["interval"] == "year"
        assert (
            stripe_price.metadata["price_type"] == stripe_constants.PriceType.BINDING_PERIOD.value
            or stripe_price.metadata["price_type"] == stripe_constants.PriceType.RECURRING.value
        )
        interval_count = (
            makeradmin_product.smallest_multiple
            if stripe_price.metadata["price_type"] == stripe_constants.PriceType.BINDING_PERIOD.value
            else 1
        )
        assert reccuring["interval_count"] == interval_count
        assert stripe_price.unit_amount == stripe_util.convert_to_stripe_amount(
            makeradmin_product.price * interval_count
        )

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
                stripe_util.deactivate_stripe_price(price)
            stripe_util.deactivate_stripe_product(stripe_product)
            return super().tearDown()

    def test_create_product(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test månad enkel",
            price=100.0,
            id=self.stripe_id_base,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product
        assert stripe_test_product.name == makeradmin_test_product.name

    def test_create_product_with_price_monthly_simple(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test månad enkel",
            price=100.0,
            id=self.stripe_id_base + 1,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.find_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        self.assertPrice(stripe_test_prices[stripe_constants.PriceType.RECURRING], makeradmin_test_product)

    def test_create_product_with_price_yearly_simple(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test år enkel",
            price=200.0,
            id=self.stripe_id_base + 2,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.find_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        self.assertPrice(stripe_test_prices[stripe_constants.PriceType.RECURRING], makeradmin_test_product)

    def test_create_product_with_price_monthly_with_binding_period(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test månad med bindingstid",
            price=300.0,
            id=self.stripe_id_base + 3,
            unit="mån",
            smallest_multiple=2,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.find_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 2
        self.assertPrice(stripe_test_prices[stripe_constants.PriceType.RECURRING], makeradmin_test_product)
        self.assertPrice(stripe_test_prices[stripe_constants.PriceType.BINDING_PERIOD], makeradmin_test_product)

    def test_activate_deactivate(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test activate deactivate",
            price=100.0,
            id=self.stripe_id_base + 4,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_util.activate_stripe_product(stripe_test_product)
        stripe_product = stripe_util.get_stripe_product(makeradmin_test_product)
        assert stripe_product.active

        stripe_util.deactivate_stripe_product(stripe_test_product)
        stripe_product = stripe_util.get_stripe_product(makeradmin_test_product)
        assert not stripe_product.active

        stripe_util.activate_stripe_product(stripe_test_product)
        stripe_product = stripe_util.get_stripe_product(makeradmin_test_product)
        assert stripe_product.active

    def test_update_product(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test update product",
            price=100.0,
            id=self.stripe_id_base + 5,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        makeradmin_test_product.name = "test name change"
        stripe_util.update_stripe_product(makeradmin_test_product, stripe_test_product)
        stripe_product = stripe_util.get_stripe_product(makeradmin_test_product)
        assert stripe_product.name == makeradmin_test_product.name

    def test_update_price(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test update price",
            price=100.0,
            id=self.stripe_id_base + 6,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.find_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        stripe_test_price = stripe_test_prices[stripe_constants.PriceType.RECURRING]

        makeradmin_test_product.price = 200.0
        new_stripe_price = stripe_util.update_stripe_price(
            makeradmin_test_product, stripe_test_price, stripe_constants.PriceType.BINDING_PERIOD
        )
        self.assertPrice(new_stripe_price, makeradmin_test_product)
        # TODO meta

        makeradmin_test_product.price = 100.0
        new_stripe_price = stripe_util.update_stripe_price(
            makeradmin_test_product, stripe_test_price, stripe_constants.PriceType.RECURRING
        )
        self.assertPrice(new_stripe_price, makeradmin_test_product)
        # TODO meta

    def test_update_price_fail(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test update price",
            price=100.0,
            id=self.stripe_id_base + 7,
            unit="mån",
            smallest_multiple=1,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.find_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.find_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        stripe_test_price = stripe_test_prices[stripe_constants.PriceType.RECURRING]

        with self.assertRaises(ValueError) as context:
            makeradmin_test_product.unit = "year"
            stripe_util.update_stripe_price(
                makeradmin_test_product, stripe_test_price, stripe_constants.PriceType.BINDING_PERIOD
            )
        self.assertTrue("not possible" in str(context.exception))

    # TODO test equal
