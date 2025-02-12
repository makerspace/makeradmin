from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Dict, List, Optional

import stripe
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
from shop.transactions import PaymentFailed, commit_fail_transaction, payment_success

logger = getLogger("makeradmin")


@dataclass(frozen=True)
class CompletedPayment(DataClassJsonMixin):
    """Used for bookkeeping for old transactions that are already completed"""

    transaction_id: int
    amount: Decimal
    charge_created: datetime
    fee: Decimal


def convert_completed_stripe_charges_to_payments(
    stripe_charges: List[Charge],
) -> Dict[int, CompletedPayment]:
    payments: Dict[int, CompletedPayment] = {}
    for charge in stripe_charges:
        if not charge.paid:
            continue

        if charge.balance_transaction is None:
            logger.error(f"Missing balance transaction in stripe charge, {charge.id}")
            raise BadRequest(f"Missing balance transaction in stripe charge, {charge.id}")
        elif not MakerspaceMetadataKeys.TRANSACTION_IDS.value in charge.metadata:
            logger.error(f"Missing transaction id in stripe charge metadata, {charge.id}")
            raise BadRequest(f"Missing transaction id in stripe charge metadata, {charge.id}")
        else:
            id = int(charge.metadata[MakerspaceMetadataKeys.TRANSACTION_IDS.value])

        payments[id] = CompletedPayment(
            transaction_id=id,
            amount=convert_from_stripe_amount(charge.amount),
            charge_created=datetime.fromtimestamp(charge.created, timezone.utc),
            fee=convert_from_stripe_amount(charge.balance_transaction.fee),
        )
    return payments


def create_fake_completed_payments_from_db(start_date: date, end_date: date) -> Dict[int, CompletedPayment]:
    payments: Dict[int, CompletedPayment] = {}
    transactions = (
        db_session.query(Transaction)
        .filter(Transaction.created_at >= start_date, Transaction.created_at <= end_date)
        .all()
    )
    for transaction in transactions:
        if transaction.status != Transaction.COMPLETED:
            continue
        payments[transaction.id] = CompletedPayment(
            transaction_id=transaction.id,
            amount=transaction.amount,
            charge_created=transaction.created_at,
            fee=Decimal(str(round(transaction.amount * Decimal(0.03), 2))),
        )
    return payments


def get_completed_payments_from_stripe(start_date: datetime, end_date: datetime) -> Dict[int, CompletedPayment]:
    if debug_mode():
        logger.warning(
            "In debug/dev mode, using fake stripe payments for accounting by generating from existing data in db"
        )
        return create_fake_completed_payments_from_db(start_date, end_date)

    try:
        stripe_charges = get_stripe_charges(start_date, end_date)
    except StripeError as e:
        raise BadRequest(message=f"Failed to fetch stripe payment intents: {e}")
    return convert_completed_stripe_charges_to_payments(stripe_charges)
