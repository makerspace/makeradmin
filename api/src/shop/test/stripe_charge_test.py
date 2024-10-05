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
from shop.completed_payment import CompletedPayment
from shop.models import StripePending, Transaction
from shop.stripe_charge import (
    get_stripe_charges,
)
from shop.stripe_constants import CURRENCY, MakerspaceMetadataKeys
from shop.stripe_customer import delete_stripe_customer, get_and_sync_stripe_customer
from shop.stripe_payment_intent import (
    pay_with_stripe,
)
from shop.stripe_util import convert_from_stripe_amount, convert_to_stripe_amount, retry
from stripe import CardError
from subscriptions_test import FakeCardPmToken, attach_and_set_payment_method
from test_aid.systest_config import STRIPE_PRIVATE_KEY
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class StripeChargeTest(FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(not STRIPE_PRIVATE_KEY, "stripe charge tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_members: List[Member] = []

    def tearDown(self) -> None:
        for makeradmin_member in self.seen_members:
            delete_stripe_customer(makeradmin_member.member_id)
            super().tearDown()

    def filter_charges_on_customers(self, stripe_charges: List[stripe.Charge]) -> Dict[int, stripe.Charge]:
        filtered_charges: Dict[int, stripe.Charge] = {}
        stripe_customers_id: List[str] = []
        for member in self.seen_members:
            stripe_customers_id.append(member.stripe_customer_id)
        for charge in stripe_charges:
            if charge.customer in stripe_customers_id:
                transaction_id = int(charge.metadata[MakerspaceMetadataKeys.TRANSACTION_IDS.value])
                filtered_charges[transaction_id] = charge
        return filtered_charges

    def test_get_charge_few(self) -> None:
        test_transactions: Dict[int, Transaction] = {}

        for i in range(3):
            member = self.db.create_member()
            self.seen_members.append(member)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=200 + (i * 10))
            payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)
            pay_with_stripe(transaction, payment_method.id, False, is_test=True)
            test_transactions[transaction.id] = transaction

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        while True:
            charges = get_stripe_charges(start_date, end_date)

            # We have to filter the completed payments because get_stripe_payments returns ALL charges,
            # including the ones from other tests and older test runs
            filtered_charges = self.filter_charges_on_customers(charges)

            assert len(filtered_charges) == len(test_transactions)

            if all(charge.balance_transaction is not None for charge in filtered_charges.values()):
                break
            else:
                # Wait for a second until stripe has generated the balance transactions
                # Stripe typically generates these after a second or two
                logger.info("Waiting for stripe to generate balance transactions...")
                time.sleep(1)

        for transaction_id, charge in filtered_charges.items():
            test_transaction = test_transactions.pop(transaction_id)
            assert transaction_id == test_transaction.id
            assert convert_from_stripe_amount(charge.amount) == test_transaction.amount
            assert charge.currency == CURRENCY
            assert charge.paid
            balance_transaction = charge.balance_transaction
            assert isinstance(balance_transaction, stripe.BalanceTransaction)
            transaction_fee = convert_from_stripe_amount(balance_transaction.fee)
            estimated_transaction_fee = test_transaction.amount * Decimal("0.025") + Decimal("1.8")
            assert math.isclose(
                transaction_fee, estimated_transaction_fee, abs_tol=test_transaction.amount * Decimal("0.025")
            )
        assert len(test_transactions) == 0

    def test_get_charge_with_declined_card(self) -> None:
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
                pay_with_stripe(transaction, payment_method.id, False, is_test=True)
            else:
                completed_payments[transaction.id] = False
                payment_method = attach_and_set_payment_method(member, FakeCardPmToken.DeclineAfterAttach)
                with self.assertRaises(CardError) as context:
                    pay_with_stripe(transaction, payment_method.id, False, is_test=True)
                self.assertTrue("declined" in str(context.exception))

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        while True:
            charges = get_stripe_charges(start_date, end_date)

            # We have to filter the completed payments because get_stripe_payments returns ALL charges,
            # including the ones from other tests and older test runs
            filtered_charges = self.filter_charges_on_customers(charges)

            # All successful payments should have a balance transaction.
            # Stripe tends to generate this a second or two after the payment charge is marked as succeeded.
            missing = False
            for charge in filtered_charges.values():
                if charge.paid and charge.balance_transaction is None:
                    missing = True
                    break

            if missing:
                # Wait for a second until stripe has generated the balance transactions
                logger.info("Waiting for stripe to generate balance transactions...")
                time.sleep(1)
            else:
                break

        assert len(filtered_charges) == len(test_transactions)
        for transaction_id, charge in filtered_charges.items():
            test_transaction = test_transactions.pop(transaction_id)
            assert transaction_id == test_transaction.id
            assert convert_from_stripe_amount(charge.amount) == test_transaction.amount
            assert charge.currency == CURRENCY

            if completed_payments[transaction_id]:
                assert charge.paid
                transaction_fee = convert_from_stripe_amount(charge.balance_transaction.fee)
                estimated_transaction_fee = test_transaction.amount * Decimal("0.025") + Decimal("1.8")
                assert math.isclose(
                    transaction_fee, estimated_transaction_fee, abs_tol=test_transaction.amount * Decimal("0.025")
                )
            else:
                assert not charge.paid
                assert charge.balance_transaction is None
        assert len(test_transactions) == 0

    def test_get_charge_date_range(self) -> None:
        # We use sleep in the test to get a range of timestamps too filter on
        # This is because we can't set the created timestamp in stripe directly

        number_of_too_old_transactions = 3
        number_of_transactions_in_range = 3
        number_of_too_new_transactions = 3

        test_transactions_in_range: Dict[int, Transaction] = {}
        test_transactions_out_of_range: Dict[int, Transaction] = {}

        # Create some charges that are too old
        for i in range(number_of_too_old_transactions):
            member = self.db.create_member()
            self.seen_members.append(member)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=200 + (i * 10))
            payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)
            pay_with_stripe(transaction, payment_method.id, False, is_test=True)
            test_transactions_out_of_range[transaction.id] = transaction

        time.sleep(5)
        start = datetime.now(timezone.utc)
        time.sleep(5)

        # Create some charges in range
        for i in range(number_of_transactions_in_range):
            member = self.db.create_member()
            self.seen_members.append(member)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=200 + (i * 10))
            payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)
            pay_with_stripe(transaction, payment_method.id, False, is_test=True)
            test_transactions_in_range[transaction.id] = transaction
            time.sleep(1)

        end = datetime.now(timezone.utc)
        time.sleep(5)

        # Create some charges that are too new
        for i in range(number_of_too_new_transactions):
            member = self.db.create_member()
            self.seen_members.append(member)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=200 + (i * 10))
            payment_method = attach_and_set_payment_method(member, FakeCardPmToken.Normal)
            pay_with_stripe(transaction, payment_method.id, False, is_test=True)
            test_transactions_out_of_range[transaction.id] = transaction

        charges = get_stripe_charges(start, end)
        filtered_charges = self.filter_charges_on_customers(charges)

        assert len(filtered_charges) == len(test_transactions_in_range)
        for charge in filtered_charges.values():
            assert charge.created >= start.timestamp()
            assert charge.created <= end.timestamp()

            transaction_id_from_charge = int(charge.metadata[MakerspaceMetadataKeys.TRANSACTION_IDS.value])
            assert transaction_id_from_charge in test_transactions_in_range
            assert not transaction_id_from_charge in test_transactions_out_of_range
