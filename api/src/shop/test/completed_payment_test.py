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
from membership.models import Member
from service.db import db_session
from shop.completed_payment import (
    convert_completed_stripe_charges_to_payments,
    get_completed_payments_from_transactions,
)
from shop.models import StripePending, Transaction
from shop.stripe_constants import CURRENCY, MakerspaceMetadataKeys, PaymentIntentStatus
from shop.stripe_util import convert_from_stripe_amount, convert_to_stripe_amount, retry
from stripe import CardError, Charge
from subscriptions_test import FakeCardPmToken, attach_and_set_payment_method
from test_aid.systest_config import STRIPE_PRIVATE_KEY
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


@dataclass
class FakeBalanceTransaction:
    fee: int


@dataclass
class FakeStripeCharge:
    balance_transaction: FakeBalanceTransaction
    paid: bool
    amount: int
    metadata: Dict[str, Any]
    created: int  # unix timestamp


class CompletedPaymentTest(FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Transaction).delete()

    def test_convert_stripe_charges_to_payments(self) -> None:
        stripe_charges: List[Charge] = []
        for i in range(5):
            paid = i % 2 == 0
            metadata = {MakerspaceMetadataKeys.TRANSACTION_IDS.value: str(i)}
            balance = FakeBalanceTransaction(fee=convert_to_stripe_amount(10 + i))
            charge = FakeStripeCharge(
                created=1701966186 + (i * 10000),
                balance_transaction=balance,
                paid=paid,
                amount=convert_to_stripe_amount(100 + (10 * i)),
                metadata=metadata,
            )
            stripe_charges.append(charge)
        completed_payments = convert_completed_stripe_charges_to_payments(stripe_charges)
        assert len(completed_payments) == 3
        for transaction_id in completed_payments:
            completed_payment = completed_payments[transaction_id]
            assert completed_payment.transaction_id == transaction_id
            assert completed_payment.amount == 100 + (10 * transaction_id)
            assert completed_payment.fee == 10 + transaction_id
            assert completed_payment.charge_created == datetime.fromtimestamp(
                1701966186 + (transaction_id * 10000), tz=timezone.utc
            )

    def test_get_completed_payments_from_transactions(self) -> None:
        number_of_transactions = 3

        member = self.db.create_member()
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        amounts: List[Decimal] = []

        for i in range(number_of_transactions):
            amounts.append(Decimal("100") + Decimal("10") * Decimal(i))
            self.db.create_transaction(id=i, member_id=member.member_id, amount=amounts[i])

        self.db.create_transaction(
            member_id=member.member_id,
            amount=Decimal("400"),
            created_at=start_date - timedelta(days=1),
        )
        self.db.create_transaction(
            member_id=member.member_id,
            amount=Decimal("600"),
            created_at=end_date + timedelta(days=1),
        )

        fake_completed = get_completed_payments_from_transactions(start_date, end_date)

        assert len(fake_completed) == number_of_transactions
        for i in range(number_of_transactions):
            assert fake_completed[i].transaction_id == i
            assert fake_completed[i].amount == amounts[i]
            assert fake_completed[i].fee == Decimal(str(round(amounts[i] * Decimal("0.03"), 2)))
            assert fake_completed[i].charge_created >= start_date.replace(tzinfo=None)
            assert fake_completed[i].charge_created <= end_date.replace(tzinfo=None)
