from logging import getLogger
from datetime import datetime, timezone, date, timedelta
from dataclasses import dataclass
from typing import Any, Dict, List
from unittest import skipIf
import math

import membership.models
import shop.models
import messages.models
import core.models
from service.db import db_session
from shop.stripe_constants import CURRENCY, MakerspaceMetadataKeys, PaymentIntentStatus
from shop.stripe_customer import delete_stripe_customer
from shop.stripe_util import convert_from_stripe_amount, convert_to_stripe_amount
from membership.models import Member
from shop.models import Transaction, StripePending
from shop.stripe_payment_intent import (
    get_stripe_payment_intents,
    convert_completed_stripe_intents_to_payments,
    pay_with_stripe,
)
import stripe
from stripe import CardError
from test_aid.test_base import FlaskTestBase, ShopTestMixin
from subscriptions_test import attach_and_set_payment_method, FakeCardPmToken

logger = getLogger("makeradmin")


@dataclass
class FakeBalanceTransaction:
    fee: int


@dataclass
class FakeStripeCharge:
    balance_transaction: FakeBalanceTransaction
    paid: bool
    amount: int


@dataclass
class FakeStripePaymentIntent:
    status: PaymentIntentStatus
    latest_charge: FakeStripeCharge
    metadata: Dict[str, Any]
    created: int  # unix timestamp


class StripePaymentIntentWithoutStripeTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    def test_convert_stripe_intents_to_payments(self) -> None:
        stripe_intents = []
        for i in range(5):
            paid = i % 2 == 0
            status = PaymentIntentStatus.SUCCEEDED if paid else PaymentIntentStatus.REQUIRES_PAYMENT_METHOD
            metadata = {MakerspaceMetadataKeys.TRANSACTION_IDS.value: str(i)}
            balance = FakeBalanceTransaction(fee=convert_to_stripe_amount(10 + i))
            charge = FakeStripeCharge(
                balance_transaction=balance, paid=paid, amount=convert_to_stripe_amount(100 + (10 * i))
            )
            intent = FakeStripePaymentIntent(
                created=1701966186 + (i * 10000), status=status, latest_charge=charge, metadata=metadata
            )
            stripe_intents.append(intent)
        payments = convert_completed_stripe_intents_to_payments(stripe_intents)
        assert len(payments) == 3
        for transaction_id in payments:
            payment = payments[transaction_id]
            assert payment.transaction_id == transaction_id
            assert payment.amount == 100 + (10 * transaction_id)
            assert payment.fee == 10 + transaction_id
            assert payment.created == datetime.fromtimestamp(1701966186 + (transaction_id * 10000), tz=timezone.utc)


class StripePaymentIntentTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(not stripe.api_key, "stripe payment intent tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_members: List[Member] = []

    def tearDown(self) -> None:
        for makeradmin_member in self.seen_members:
            delete_stripe_customer(makeradmin_member.member_id)
            return super().tearDown()

    def filter_intents_on_customers(
        self, stripe_intents: List[stripe.PaymentIntent]
    ) -> Dict[int, stripe.PaymentIntent]:
        filtered_intents: Dict[int, stripe.PaymentIntent] = {}
        stripe_customers_id: List[str] = []
        for member in self.seen_members:
            stripe_customers_id.append(member.stripe_customer_id)
        for intent in stripe_intents:
            if intent.customer in stripe_customers_id:
                transaction_id = int(intent.metadata[MakerspaceMetadataKeys.TRANSACTION_IDS.value])
                filtered_intents[transaction_id] = intent
        return filtered_intents

    def test_pay_with_stripe_success(self) -> None:
        member = self.db.create_member()
        self.seen_members.append(member)
        transaction = self.db.create_transaction(member_id=member.member_id, amount=200)
        payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)

        stripe_intent = pay_with_stripe(transaction, payment_method.id, False)

        assert stripe_intent.status == PaymentIntentStatus.SUCCEEDED
        assert transaction.status == Transaction.COMPLETED
        assert stripe_intent.amount == convert_to_stripe_amount(transaction.amount)
        assert stripe_intent.currency == CURRENCY
        stripe_pending = (
            db_session.query(StripePending).filter(StripePending.transaction_id == transaction.id).one_or_none()
        )
        assert stripe_pending.stripe_token == stripe_intent.id

    def test_pay_with_stripe_fail(self) -> None:
        member = self.db.create_member()
        self.seen_members.append(member)
        transaction = self.db.create_transaction(member_id=member.member_id, amount=200)
        payment_method = attach_and_set_payment_method(member, FakeCardPmToken.DeclineAfterAttach)

        with self.assertRaises(CardError) as context:
            pay_with_stripe(transaction, payment_method.id, False)
        self.assertTrue("declined" in str(context.exception))

    def test_get_payment_intent_few(self) -> None:
        test_transactions: Dict[int, Transaction] = {}
        test_intents: Dict[int, stripe.PaymentIntent] = {}

        for i in range(3):
            member = self.db.create_member()
            self.seen_members.append(member)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=200 + (i * 10))
            payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)
            test_intents[transaction.id] = pay_with_stripe(transaction, payment_method.id, False)
            test_transactions[transaction.id] = transaction

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        intents = get_stripe_payment_intents(start_date, end_date)

        # We have to filter the completed payments because get_stripe_payments returns ALL intents,
        # including the ones from other tests and older test runs
        filtered_intents = self.filter_intents_on_customers(intents)

        assert len(filtered_intents) == len(test_transactions)
        for transaction_id in filtered_intents:
            test_transaction = test_transactions.pop(transaction_id)
            assert transaction_id == test_transaction.id
            assert convert_from_stripe_amount(test_intents[transaction_id].amount) == test_transaction.amount
            assert convert_from_stripe_amount(filtered_intents[transaction_id].amount) == test_transaction.amount
            assert filtered_intents[transaction_id].currency == CURRENCY
            assert filtered_intents[transaction_id].status == PaymentIntentStatus.SUCCEEDED.value
            transaction_fee = convert_from_stripe_amount(
                filtered_intents[transaction_id].latest_charge.balance_transaction.fee
            )
            estimated_transaction_fee = test_transaction.amount * 0.025 + 1.8
            assert math.isclose(transaction_fee, estimated_transaction_fee, abs_tol=test_transaction.amount * 0.025)
        assert len(test_transactions) == 0

    def test_get_payment_intent_with_declined_card(self) -> None:
        test_transactions: Dict[int, Transaction] = {}
        completed_payments: Dict[int, bool] = {}

        for i in range(5):
            member = self.db.create_member()
            self.seen_members.append(member)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=200 + (i * 10))
            test_transactions[transaction.id] = transaction
            if i % 2 == 0:
                completed_payments[transaction.id] = True
                payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)
                pay_with_stripe(transaction, payment_method.id, False)
            else:
                completed_payments[transaction.id] = False
                payment_method = attach_and_set_payment_method(member, FakeCardPmToken.DeclineAfterAttach)
                with self.assertRaises(CardError) as context:
                    pay_with_stripe(transaction, payment_method.id, False)
                self.assertTrue("declined" in str(context.exception))

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        intents = get_stripe_payment_intents(start_date, end_date)

        # We have to filter the completed payments because get_stripe_payments returns ALL intents,
        # including the ones from other tests and older test runs
        filtered_intents = self.filter_intents_on_customers(intents)

        logger.info(f"***********************")
        logger.info(completed_payments)

        assert len(filtered_intents) == len(test_transactions)
        for transaction_id in filtered_intents:
            test_transaction = test_transactions.pop(transaction_id)
            assert transaction_id == test_transaction.id
            assert convert_from_stripe_amount(filtered_intents[transaction_id].amount) == test_transaction.amount
            assert filtered_intents[transaction_id].currency == CURRENCY

            if completed_payments[transaction_id]:
                assert filtered_intents[transaction_id].status == PaymentIntentStatus.SUCCEEDED.value
                transaction_fee = convert_from_stripe_amount(
                    filtered_intents[transaction_id].latest_charge.balance_transaction.fee
                )
                estimated_transaction_fee = test_transaction.amount * 0.025 + 1.8
                assert math.isclose(transaction_fee, estimated_transaction_fee, abs_tol=test_transaction.amount * 0.025)
            else:
                assert filtered_intents[transaction_id].status != PaymentIntentStatus.SUCCEEDED.value
                assert filtered_intents[transaction_id].latest_charge.balance_transaction is None
        assert len(test_transactions) == 0

    # TODO test with subscriptions
