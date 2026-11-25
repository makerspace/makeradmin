from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Dict, List, Optional

from dataclasses_json import DataClassJsonMixin
from membership.models import Member
from service.config import debug_mode
from service.db import db_session
from service.error import EXCEPTION, BadRequest, InternalServerError
from stripe import CardError, Charge, InvalidRequestError, PaymentIntent, StripeError

from shop.models import Transaction
from shop.stripe_charge import get_stripe_charges
from shop.stripe_constants import (
    CURRENCY,
    MakerspaceMetadataKeys,
    PaymentIntentNextActionType,
    PaymentIntentStatus,
    SetupFutureUsage,
)
from shop.stripe_customer import get_and_sync_stripe_customer
from shop.stripe_util import convert_from_stripe_amount, convert_to_stripe_amount, replace_default_payment_method, retry

logger = getLogger("makeradmin")


@dataclass(frozen=True)
class CompletedPayment(DataClassJsonMixin):
    """Used for bookkeeping for old transactions that are already completed"""

    transaction_id: int
    amount: Decimal
    charge_created: datetime
    fee: Decimal


@dataclass(frozen=True)
class CourseBookingPayment:
    """A paid course booking, charged by the course booking app on the shared stripe account."""

    booking_id: str
    # Net of refunds. Zero for a fully refunded booking, which still costs its fee.
    amount: Decimal
    charge_created: datetime
    fee: Decimal


@dataclass(frozen=True)
class StripePayments:
    """All income found in stripe for a period, split by the system that charged it."""

    # Keyed on makeradmin transaction id.
    transactions: Dict[int, CompletedPayment]
    course_bookings: List[CourseBookingPayment]


# Set by the course booking app on the charges it creates.
COURSE_BOOKING_ID_METADATA_KEY = "booking_id"


def convert_completed_stripe_charges_to_payments(stripe_charges: List[Charge]) -> StripePayments:
    """Sort paid stripe charges into makeradmin transaction payments and course bookings.

    Contract: every paid charge must be attributable to one of the two. An unknown charge
    raises [BadRequest], since skipping it would silently leave income out of the books.
    """
    payments: Dict[int, CompletedPayment] = {}
    course_bookings: List[CourseBookingPayment] = []
    for charge in stripe_charges:
        if not charge.paid:
            continue

        if charge.balance_transaction is None:
            logger.error(f"Missing balance transaction in stripe charge, {charge.id}")
            raise BadRequest(f"Missing balance transaction in stripe charge, {charge.id}")
        fee = convert_from_stripe_amount(charge.balance_transaction.fee)
        charge_created = datetime.fromtimestamp(charge.created, timezone.utc)

        transaction_id = charge.metadata.get(MakerspaceMetadataKeys.TRANSACTION_IDS.value)
        if transaction_id is None and charge.payment_intent is not None:
            transaction_id = charge.payment_intent.metadata.get(MakerspaceMetadataKeys.TRANSACTION_IDS.value)

        if transaction_id is not None:
            id = int(transaction_id)
            payments[id] = CompletedPayment(
                transaction_id=id,
                amount=convert_from_stripe_amount(charge.amount),
                charge_created=charge_created,
                fee=fee,
            )
            continue

        booking_id = charge.metadata.get(COURSE_BOOKING_ID_METADATA_KEY)
        if booking_id is not None:
            course_bookings.append(
                CourseBookingPayment(
                    booking_id=str(booking_id),
                    amount=convert_from_stripe_amount(charge.amount - charge.amount_refunded),
                    charge_created=charge_created,
                    fee=fee,
                )
            )
            continue

        raise BadRequest(
            f"Stripe charge {charge.id} is paid but belongs to neither a makeradmin transaction nor a course booking"
        )

    return StripePayments(transactions=payments, course_bookings=course_bookings)


def create_fake_completed_payments_from_db(start_date: date, end_date: date) -> Dict[int, CompletedPayment]:
    payments: Dict[int, CompletedPayment] = {}
    transactions = (
        db_session.query(Transaction)
        .filter(Transaction.created_at >= start_date, Transaction.created_at <= end_date)
        .all()
    )
    for transaction in transactions:
        if transaction.status != Transaction.Status.completed or transaction.amount == 0:
            continue
        payments[transaction.id] = CompletedPayment(
            transaction_id=transaction.id,
            amount=transaction.amount,
            charge_created=transaction.created_at,
            fee=Decimal(str(round(transaction.amount * Decimal(0.03), 2))),
        )
    return payments


def get_completed_payments_from_stripe(start_date: datetime, end_date: datetime) -> StripePayments:
    if debug_mode():
        logger.warning(
            "In debug/dev mode, using fake stripe payments for accounting by generating from existing data in db"
        )
        return StripePayments(
            transactions=create_fake_completed_payments_from_db(start_date, end_date), course_bookings=[]
        )

    try:
        stripe_charges = get_stripe_charges(start_date, end_date)
    except StripeError as e:
        raise BadRequest(message=f"Failed to fetch stripe payment intents: {e}")
    return convert_completed_stripe_charges_to_payments(stripe_charges)
