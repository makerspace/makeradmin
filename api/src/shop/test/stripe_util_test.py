from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import core.models
import membership.models
import messages.models
import shop.models
import stripe
from shop import stripe_constants, stripe_util
from shop.models import Product
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
