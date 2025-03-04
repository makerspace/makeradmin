import math
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import core.models
import membership.models
import messages.models
import shop.models
import stripe
from membership.models import Member
from service.db import db_session
from shop.models import StripePending, Transaction
from shop.stripe_constants import CURRENCY, MakerspaceMetadataKeys, PaymentIntentStatus
from shop.stripe_customer import delete_stripe_customer, get_and_sync_stripe_customer
from shop.stripe_payment_intent import pay_with_stripe
from shop.stripe_util import convert_from_stripe_amount, convert_to_stripe_amount, retry
from shop.transactions import PaymentFailed
from subscriptions_test import FakeCardPmToken, attach_and_set_payment_method
from test_aid.systest_config import STRIPE_PRIVATE_KEY
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class StripePaymentIntentTest(FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(not STRIPE_PRIVATE_KEY, "stripe payment intent tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_members: List[Member] = []

    def tearDown(self) -> None:
        for makeradmin_member in self.seen_members:
            delete_stripe_customer(makeradmin_member.member_id)
            super().tearDown()

    def test_pay_with_stripe_success(self) -> None:
        member = self.db.create_member()
        self.seen_members.append(member)
        transaction = self.db.create_transaction(member_id=member.member_id, amount=200)
        payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)

        stripe_intent = pay_with_stripe(transaction, payment_method.id, False, is_test=True)

        assert stripe_intent.status == PaymentIntentStatus.SUCCEEDED
        assert transaction.status == Transaction.Status.completed
        assert stripe_intent.amount == convert_to_stripe_amount(transaction.amount)
        assert stripe_intent.currency == CURRENCY
        stripe_pending = db_session.query(StripePending).filter(StripePending.transaction_id == transaction.id).one()
        assert stripe_pending.stripe_token == stripe_intent.id

    def test_pay_with_stripe_fail(self) -> None:
        member = self.db.create_member()
        self.seen_members.append(member)
        transaction = self.db.create_transaction(member_id=member.member_id, amount=200)
        payment_method = attach_and_set_payment_method(member, FakeCardPmToken.DeclineAfterAttach)

        with self.assertRaises(PaymentFailed) as context:
            pay_with_stripe(transaction, payment_method.id, False, is_test=True)
        self.assertTrue("declined" in str(context.exception.message))
