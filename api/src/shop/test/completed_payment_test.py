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
from service.error import BadRequest
from shop.completed_payment import (
    CourseBookingPayment,
    convert_completed_stripe_charges_to_payments,
    create_fake_completed_payments_from_db,
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
    id: str = "ch_fake"
    payment_intent: Any = None
    amount_refunded: int = 0


@dataclass
class FakePaymentIntent:
    metadata: Dict[str, Any]


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
        completed_payments = convert_completed_stripe_charges_to_payments(stripe_charges).transactions
        assert len(completed_payments) == 3
        for transaction_id in completed_payments:
            completed_payment = completed_payments[transaction_id]
            assert completed_payment.transaction_id == transaction_id
            assert completed_payment.amount == 100 + (10 * transaction_id)
            assert completed_payment.fee == 10 + transaction_id
            assert completed_payment.charge_created == datetime.fromtimestamp(
                1701966186 + (transaction_id * 10000), tz=timezone.utc
            )

    def fake_charge(self, **kwargs: Any) -> Charge:
        defaults: Dict[str, Any] = dict(
            created=1701966186,
            balance_transaction=FakeBalanceTransaction(fee=convert_to_stripe_amount(10)),
            paid=True,
            amount=convert_to_stripe_amount(100),
            metadata={},
        )
        return FakeStripeCharge(**(defaults | kwargs))  # type: ignore[return-value]

    def test_transaction_id_is_read_from_payment_intent_when_missing_on_charge(self) -> None:
        intent = FakePaymentIntent(metadata={MakerspaceMetadataKeys.TRANSACTION_IDS.value: "7"})

        payments = convert_completed_stripe_charges_to_payments([self.fake_charge(payment_intent=intent)])

        assert list(payments.transactions.keys()) == [7]
        assert payments.course_bookings == []

    def test_course_booking_charges_are_separated_from_transactions(self) -> None:
        # Regression: course booking charges on the shared stripe account failed the whole
        # export with KeyError 'makerspace_transaction_ids'.
        booking_metadata = {"booking_id": "b1", "makerspace_member_id": "1"}
        charges = [
            self.fake_charge(metadata={MakerspaceMetadataKeys.TRANSACTION_IDS.value: "1"}),
            self.fake_charge(
                metadata=booking_metadata,
                payment_intent=FakePaymentIntent(metadata=booking_metadata),
                amount=convert_to_stripe_amount(150),
                balance_transaction=FakeBalanceTransaction(fee=convert_to_stripe_amount(4)),
            ),
        ]

        payments = convert_completed_stripe_charges_to_payments(charges)

        assert list(payments.transactions.keys()) == [1]
        assert payments.course_bookings == [
            CourseBookingPayment(
                booking_id="b1",
                amount=Decimal("150.00"),
                charge_created=datetime.fromtimestamp(1701966186, tz=timezone.utc),
                fee=Decimal("4.00"),
            )
        ]

    def test_course_booking_amount_is_net_of_refunds(self) -> None:
        metadata = {"booking_id": "b1"}
        charges = [
            self.fake_charge(metadata=metadata, amount=10000, amount_refunded=10000),
            self.fake_charge(metadata=metadata, amount=20000, amount_refunded=5000),
        ]

        bookings = convert_completed_stripe_charges_to_payments(charges).course_bookings

        # A fully refunded booking is kept, as stripe does not return its fee.
        assert [(b.amount, b.fee) for b in bookings] == [
            (Decimal("0.00"), Decimal("10.00")),
            (Decimal("150.00"), Decimal("10.00")),
        ]

    def test_unattributable_charge_fails_export(self) -> None:
        with self.assertRaises(BadRequest):
            convert_completed_stripe_charges_to_payments([self.fake_charge(payment_intent=FakePaymentIntent({}))])

    def test_create_fake_completed_payments_from_db(self) -> None:
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

        fake_completed = create_fake_completed_payments_from_db(start_date, end_date)

        assert len(fake_completed) == number_of_transactions
        for i in range(number_of_transactions):
            assert fake_completed[i].transaction_id == i
            assert fake_completed[i].amount == amounts[i]
            assert fake_completed[i].fee == Decimal(str(round(amounts[i] * Decimal("0.03"), 2)))
            assert fake_completed[i].charge_created >= start_date.replace(tzinfo=None)
            assert fake_completed[i].charge_created <= end_date.replace(tzinfo=None)
