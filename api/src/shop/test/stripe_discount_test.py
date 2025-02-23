from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import core.models
import membership.models
import messages.models
import shop.models
import stripe
from shop.models import Discount, Product
from shop.stripe_constants import (
    MakerspaceMetadataKeys as MSMetaKeys,
)
from shop.stripe_discounts import (
    _create_stripe_coupon,
    _get_coupon_applies_to_stripe_product_ids,
    _get_stripe_equivalent_to_duration_for_discount,
    delete_stripe_coupon,
    get_and_sync_stripe_coupon,
    get_or_create_stripe_coupon,
    get_price_level_for_member,
    replace_stripe_coupon,
)
from shop.stripe_util import are_metadata_dicts_equivalent, retry
from test_aid.systest_config import STRIPE_PRIVATE_KEY
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class StripeDiscountWithoutStripeTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    @classmethod
    def setUpClass(self) -> None:
        super().setUpClass()

    def test_get_stripe_equivalent_to_duration_for_discount_repeating(self) -> None:
        makeradmin_test_discount = self.db.create_discount(
            percent_off=50, duration=Discount.REPEATING, duration_in_months=3
        )
        discount, discount_in_months = _get_stripe_equivalent_to_duration_for_discount(makeradmin_test_discount)
        assert discount == Discount.REPEATING
        assert discount_in_months == 3

    def test_get_stripe_equivalent_to_duration_for_discount_forever(self) -> None:
        makeradmin_test_discount = self.db.create_discount(
            percent_off=50, duration=Discount.FOREVER, duration_in_months=None
        )
        discount, discount_in_months = _get_stripe_equivalent_to_duration_for_discount(makeradmin_test_discount)
        assert discount == Discount.FOREVER
        assert discount_in_months is None

    def test_get_stripe_equivalent_to_duration_for_discount_negative_duration(self) -> None:
        makeradmin_test_discount = self.db.create_discount(
            percent_off=50, duration=Discount.REPEATING, duration_in_months=-3
        )
        with self.assertRaises(RuntimeError):
            _get_stripe_equivalent_to_duration_for_discount(makeradmin_test_discount)

    def test_get_stripe_equivalent_to_duration_for_discount_forever_has_duration_in_months(self) -> None:
        makeradmin_test_discount = self.db.create_discount(
            percent_off=50, duration=Discount.FOREVER, duration_in_months=3
        )
        with self.assertRaises(RuntimeError):
            _get_stripe_equivalent_to_duration_for_discount(makeradmin_test_discount)

    def test_get_coupon_applies_to_stripe_product_ids(self) -> None:
        number_of_products = 3

        makeradmin_test_discount = self.db.create_discount()
        test_products: List[Product] = []
        for i in range(number_of_products):
            product = self.db.create_product(price=100 + i)
            test_products.append(product)
            self.db.create_discount_product_mapping(product_id=product.id, discount_id=makeradmin_test_discount.id)

        stripe_product_dict = _get_coupon_applies_to_stripe_product_ids(makeradmin_test_discount)
        coupon_applies_to_products = stripe_product_dict["products"]

        assert set(test_products) == set(coupon_applies_to_products)


class StripeDiscountTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(not STRIPE_PRIVATE_KEY, "stripe discounts tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_discounts: List[Discount] = []

    def tearDown(self) -> None:
        for makeradmin_discounnt in self.seen_discounts:
            delete_stripe_coupon(makeradmin_discounnt.id)
            return super().tearDown()

    @staticmethod
    def assertDiscount(makeradmin_discount: Discount, stripe_test_coupon: stripe.Coupon) -> None:
        # TODO
        assert stripe_test_coupon
        assert stripe_test_coupon.name == makeradmin_discount.name
        assert stripe_test_coupon.percent_off == makeradmin_discount.percent_off

    def test_create_coupon_simple(self) -> None:
        makeradmin_test_discount = self.db.create_discount(percent_off=50)
        self.seen_discounts.append(makeradmin_test_discount)

        stripe_test_customer = get_or_create_stripe_coupon(makeradmin_test_discount)
        self.assertDiscount(makeradmin_test_discount, stripe_test_customer)
