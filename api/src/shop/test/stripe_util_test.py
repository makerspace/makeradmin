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
        assert recurring.interval == "month"
        assert recurring.interval_count == 1

    def test_makeradmin_to_stripe_recurring_binding(self) -> None:
        makeradmin_test_product = self.db.create_product(
            unit="mån",
            smallest_multiple=3,
        )
        recurring = stripe_util.makeradmin_to_stripe_recurring(
            makeradmin_test_product, stripe_constants.PriceType.BINDING_PERIOD
        )
        assert recurring.interval == "month"
        assert recurring.interval_count == 3

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
            recurring = stripe_util.StripeRecurring(interval="month", interval_count=multiple)
            stripe_amount = stripe_util.stripe_amount_from_makeradmin_product(makeradmin_test_product, recurring)
            assert stripe_amount == multiple * price * stripe_constants.STRIPE_CURRENTY_BASE


class StripeUtilWithStripeTest(ShopTestMixin, FlaskTestBase):
    # The products id in makeradmin have to be unique in each test to prevent race conditions
    # Some of the tests here will generate new objects in stripe. They are all ran in test mode
    # You can clear the test area in stripe's developer dashboard.

    models = [membership.models, messages.models, shop.models, core.models]
    base_stripe_id = 5100

    @skipIf(not stripe.api_key, "stripe util tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_products: List[Product] = []
        self.subscription_category = self.db.create_category(name="Subscriptions")
        self.not_subscription_category = self.db.create_category(name="Not Subscriptions")

    @staticmethod
    def assertPrice(
        stripe_price: stripe.Price, makeradmin_product: Product, price_type: stripe_constants.PriceType
    ) -> None:
        assert stripe_price.currency == stripe_constants.CURRENCY
        if price_type == stripe_constants.PriceType.FIXED_PRICE:
            assert stripe_price.type == "one_time"
            interval_count = 1
        else:
            assert stripe_price.type == "recurring"
            reccuring = stripe_price.recurring
            if "mån" in makeradmin_product.unit:
                assert reccuring["interval"] == "month"
            else:
                assert reccuring["interval"] == "year"
            interval_count = (
                makeradmin_product.smallest_multiple
                if stripe_price.metadata["price_type"] == stripe_constants.PriceType.BINDING_PERIOD.value
                else 1
            )
            assert reccuring["interval_count"] == interval_count
        assert stripe_price.metadata["price_type"] == price_type.value
        assert stripe_price.unit_amount == stripe_util.convert_to_stripe_amount(
            makeradmin_product.price * interval_count
        )

    def tearDown(self) -> None:
        # It is not possible to delete prices through the api so we set them as inactive instead
        for makeradmin_product in self.seen_products:
            stripe_product = stripe_util.get_stripe_product(makeradmin_product)
            if stripe_product is None:
                continue
            if stripe_product.active:
                stripe_util.deactivate_stripe_product(stripe_product)
            stripe_prices = stripe_util.get_stripe_prices(stripe_product)
            if stripe_prices is None:
                continue
            for price in stripe_prices:
                if price.active:
                    stripe_util.deactivate_stripe_price(price)
            return super().tearDown()

    def test_create_product(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test månad enkel",
            price=100.0,
            id=self.base_stripe_id,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product
        assert stripe_test_product.name == makeradmin_test_product.name

    def test_create_product_with_price_regular(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test regular product",
            price=100.0,
            id=self.base_stripe_id + 1,
            unit="st",
            smallest_multiple=1,
            category_id=self.not_subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        self.assertPrice(
            stripe_test_prices[stripe_constants.PriceType.FIXED_PRICE],
            makeradmin_test_product,
            stripe_constants.PriceType.FIXED_PRICE,
        )

    def test_create_product_with_price_monthly_simple(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test månad enkel",
            price=100.0,
            id=self.base_stripe_id + 2,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        self.assertPrice(
            stripe_test_prices[stripe_constants.PriceType.RECURRING],
            makeradmin_test_product,
            stripe_constants.PriceType.RECURRING,
        )

    def test_create_product_with_price_yearly_simple(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test år enkel",
            price=200.0,
            id=self.base_stripe_id + 3,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        self.assertPrice(
            stripe_test_prices[stripe_constants.PriceType.RECURRING],
            makeradmin_test_product,
            stripe_constants.PriceType.RECURRING,
        )

    def test_create_product_with_price_monthly_with_binding_period(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test månad med bindingstid",
            price=300.0,
            id=self.base_stripe_id + 4,
            unit="mån",
            smallest_multiple=2,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 2
        self.assertPrice(
            stripe_test_prices[stripe_constants.PriceType.RECURRING],
            makeradmin_test_product,
            stripe_constants.PriceType.RECURRING,
        )
        self.assertPrice(
            stripe_test_prices[stripe_constants.PriceType.BINDING_PERIOD],
            makeradmin_test_product,
            stripe_constants.PriceType.BINDING_PERIOD,
        )

    def test_activate_deactivate(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test activate deactivate",
            price=100.0,
            id=self.base_stripe_id + 5,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
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
            id=self.base_stripe_id + 6,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        makeradmin_test_product.name = "test name change"
        stripe_util.update_stripe_product(makeradmin_test_product, stripe_test_product)
        stripe_product = stripe_util.get_stripe_product(makeradmin_test_product)
        assert stripe_product.name == makeradmin_test_product.name

    def test_get_sync_product(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test update product",
            price=100.0,
            id=self.base_stripe_id + 6,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_and_sync_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        makeradmin_test_product.name = "test name change"
        stripe_product = stripe_util.get_and_sync_stripe_product(makeradmin_test_product)
        assert stripe_product
        assert stripe_product.name == makeradmin_test_product.name

    def test_replace_price(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test update price",
            price=100.0,
            id=self.base_stripe_id + 7,
            unit="mån",
            smallest_multiple=1,
            category_id=self.not_subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1
        stripe_test_price = stripe_test_prices[stripe_constants.PriceType.FIXED_PRICE]

        makeradmin_test_product.price = 200.0
        new_stripe_price = stripe_util.replace_stripe_price(
            makeradmin_test_product, stripe_test_price, stripe_constants.PriceType.FIXED_PRICE
        )
        self.assertPrice(new_stripe_price, makeradmin_test_product, stripe_constants.PriceType.FIXED_PRICE)

        makeradmin_test_product.price = 100.0
        new_stripe_price = stripe_util.replace_stripe_price(
            makeradmin_test_product, stripe_test_price, stripe_constants.PriceType.FIXED_PRICE
        )
        self.assertPrice(new_stripe_price, makeradmin_test_product, stripe_constants.PriceType.FIXED_PRICE)

    def test_get_sync_price(self) -> None:
        makeradmin_test_product = self.db.create_product(
            name="test update price",
            price=100.0,
            id=self.base_stripe_id + 7,
            unit="mån",
            smallest_multiple=1,
            category_id=self.not_subscription_category.id,
        )
        self.seen_products.append(makeradmin_test_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_and_sync_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1

        makeradmin_test_product.price = 200.0
        new_stripe_prices = stripe_util.get_and_sync_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        self.assertPrice(
            new_stripe_prices[stripe_constants.PriceType.FIXED_PRICE],
            makeradmin_test_product,
            stripe_constants.PriceType.FIXED_PRICE,
        )

        makeradmin_test_product.price = 100.0
        new_stripe_prices = stripe_util.get_and_sync_stripe_prices_for_product(
            makeradmin_test_product, stripe_test_product
        )
        self.assertPrice(
            new_stripe_prices[stripe_constants.PriceType.FIXED_PRICE],
            makeradmin_test_product,
            stripe_constants.PriceType.FIXED_PRICE,
        )

    def test_equal_product(self) -> None:
        makeradmin_test_eq_product = self.db.create_product(
            name="test eq price",
            price=200.0,
            id=self.base_stripe_id + 8,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        makeradmin_test_not_eq_product = self.db.create_product(
            name="test not eq price",
            price=200.0,
            id=self.base_stripe_id - 1,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )

        self.seen_products.append(makeradmin_test_eq_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_eq_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_eq_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1

        assert stripe_util.eq_makeradmin_stripe_product(makeradmin_test_eq_product, stripe_test_product)
        assert not stripe_util.eq_makeradmin_stripe_product(makeradmin_test_not_eq_product, stripe_test_product)

    def test_equal_price(self) -> None:
        makeradmin_test_eq_product = self.db.create_product(
            name="test eq price",
            price=200.0,
            id=self.base_stripe_id + 9,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        product_not_eq_price = self.db.create_product(
            name="test not eq price",
            price=210.0,
            id=self.base_stripe_id - 1,
            unit="mån",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        product_not_eq_unit = self.db.create_product(
            name="test not eq unit",
            price=200.0,
            id=self.base_stripe_id - 2,
            unit="year",
            smallest_multiple=1,
            category_id=self.subscription_category.id,
        )
        product_not_eq_id = self.db.create_product(
            name="test not eq mult",
            price=200.0,
            id=self.base_stripe_id - 3,
            unit="mån",
            smallest_multiple=2,
            category_id=self.subscription_category.id,
        )
        product_not_eq_cat = self.db.create_product(
            name="test not eq category",
            price=200.0,
            id=self.base_stripe_id - 4,
            unit="mån",
            smallest_multiple=2,
            category_id=self.not_subscription_category.id,
        )
        makeradmin_test_products_not_eq = [
            product_not_eq_price,
            product_not_eq_unit,
            product_not_eq_id,
            product_not_eq_cat,
        ]
        price_types = [
            stripe_constants.PriceType.RECURRING,
            stripe_constants.PriceType.RECURRING,
            stripe_constants.PriceType.BINDING_PERIOD,
            stripe_constants.PriceType.FIXED_PRICE,
        ]
        self.seen_products.append(makeradmin_test_eq_product)
        stripe_test_product = stripe_util.get_or_create_stripe_product(makeradmin_test_eq_product)
        assert stripe_test_product

        stripe_test_prices = stripe_util.get_or_create_stripe_prices_for_product(
            makeradmin_test_eq_product, stripe_test_product
        )
        assert stripe_test_prices
        assert len(stripe_test_prices) == 1

        assert stripe_util.eq_makeradmin_stripe_price(
            makeradmin_test_eq_product,
            stripe_test_prices[stripe_constants.PriceType.RECURRING],
            stripe_constants.PriceType.RECURRING,
        )
        for product, price_type in zip(makeradmin_test_products_not_eq, price_types):
            assert not stripe_util.eq_makeradmin_stripe_price(
                product,
                stripe_test_prices[stripe_constants.PriceType.RECURRING],
                price_type,
            )
