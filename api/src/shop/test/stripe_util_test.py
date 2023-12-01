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
