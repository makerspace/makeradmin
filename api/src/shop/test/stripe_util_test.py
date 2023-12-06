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

    def test_are_metadata_dicts_equivalent_empty(self) -> None:
        dict_A = {}
        dict_B = {}
        assert stripe_util.are_metadata_dicts_equivalent(dict_A, dict_B)

    def test_are_metadata_dicts_equivalent_identical(self) -> None:
        dict_A = {
            "makerspace_member_number": "1430186",
            "makerspace_pending_member": "not_pending",
            "makerspace_user_id": "1",
        }
        dict_B = {
            "makerspace_member_number": "1430186",
            "makerspace_pending_member": "not_pending",
            "makerspace_user_id": "1",
        }
        assert stripe_util.are_metadata_dicts_equivalent(dict_A, dict_B)

    def test_are_metadata_dicts_equivalent_not_same(self) -> None:
        dict_A = {
            "makerspace_member_number": "1430186",
            "makerspace_pending_member": "not_pending",
            "makerspace_user_id": "1",
        }
        dict_B = {
            "makerspace_member_number": "143",
            "makerspace_pending_member": "not_pending",
            "makerspace_user_id": "1",
        }
        assert not stripe_util.are_metadata_dicts_equivalent(dict_A, dict_B)

    def test_are_metadata_dicts_equivalent_something_with_empty(self) -> None:
        dict_A = {
            "makerspace_member_number": "1430186",
            "makerspace_pending_member": "not_pending",
            "makerspace_user_id": "1",
        }
        dict_B = {}
        assert not stripe_util.are_metadata_dicts_equivalent(dict_A, dict_B)

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
