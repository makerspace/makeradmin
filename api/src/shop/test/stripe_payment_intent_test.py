from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import membership.models
import shop.models
import messages.models
import core.models
from shop.stripe_constants import CURRENCY
from shop.stripe_util import convert_from_stripe_amount, convert_to_stripe_amount
from membership.models import Member
from shop.stripe_payment_intent import get_all_stripe_payment_intents, pay_with_stripe
import stripe
from test_aid.test_base import FlaskTestBase, ShopTestMixin
from subscriptions_test import attach_and_set_payment_method, FakeCardPmToken

logger = getLogger("makeradmin")


class StripePaymentIntentTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(not stripe.api_key, "stripe util tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_members: List[Member] = []

    def tearDown(self) -> None:
        for makeradmin_member in self.seen_members:
            delete_stripe_customer(makeradmin_member.member_id)
            return super().tearDown()

    def test_pay_with_stripe(self) -> None:
        member = self.db.create_member()
        self.seen_members.append(member)
        transaction = self.db.create_transaction(member_id=member.member_id, amount=200)
        payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)

        stripe_intent = pay_with_stripe(transaction, payment_method.id, False)
        logger.info("*****************")
        logger.info(stripe_intent)
        assert stripe_intent.amount == convert_to_stripe_amount(transaction.amount)
        assert stripe_intent.currency == CURRENCY

    # TODO test get all intents

    # TODO test with subscriptions

    # TODO test with some failed payments and stuff
