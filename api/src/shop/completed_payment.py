from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional

from dataclasses_json import DataClassJsonMixin
from membership.models import Member
from service.config import debug_mode, get_payment_provider
from service.db import db_session
from service.error import EXCEPTION, BadRequest, InternalServerError
from stripe import CardError, Charge, InvalidRequestError, PaymentIntent, StripeError

from shop.accounting.accounting import (
    AccountingError,
    diff_transactions_and_completed_payments,
)
from shop.models import Transaction
from shop.stripe_charge import get_stripe_charges
from shop.stripe_constants import (
    CURRENCY,
    MakerspaceMetadataKeys,
)
from shop.stripe_util import convert_from_stripe_amount, retry

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
            intent = retry(lambda: PaymentIntent.retrieve(charge.payment_intent))
            id = int(intent.metadata[MakerspaceMetadataKeys.TRANSACTION_IDS.value])
        else:
            id = int(charge.metadata[MakerspaceMetadataKeys.TRANSACTION_IDS.value])

        payments[id] = CompletedPayment(
            transaction_id=id,
            amount=convert_from_stripe_amount(charge.amount),
            charge_created=datetime.fromtimestamp(charge.created, timezone.utc),
            fee=convert_from_stripe_amount(charge.balance_transaction.fee),
        )
    return payments


def get_completed_payments(
    start_date: datetime, end_date: datetime, transactions: List[Transaction]
) -> Dict[int, CompletedPayment]:
    if debug_mode() or get_payment_provider() is None:
        completed_payments = get_completed_payments_from_transactions(transactions)
    elif get_payment_provider() == "stripe":
        completed_payments = get_completed_payments_from_stripe(start_date, end_date)
        diff = diff_transactions_and_completed_payments(transactions, completed_payments)
        if len(diff) > 0:
            raise AccountingError(f"Transactions and completed payments do not match, {diff}")
    else:
        raise InternalServerError(f"Unknown payment provider: {get_payment_provider()}")

    return completed_payments


def get_completed_payments_from_transactions(transactions: List[Transaction]) -> Dict[int, CompletedPayment]:
    payments: Dict[int, CompletedPayment] = {}
    for transaction in transactions:
        if transaction.status != Transaction.COMPLETED:
            continue
        payments[transaction.id] = CompletedPayment(
            transaction_id=transaction.id,
            amount=transaction.amount,
            charge_created=transaction.created_at,
            fee=Decimal(0),
        )
    return payments


def get_completed_payments_from_stripe(start_date: datetime, end_date: datetime) -> Dict[int, CompletedPayment]:
    try:
        stripe_charges = get_stripe_charges(start_date, end_date)
    except StripeError as e:
        raise BadRequest(message=f"Failed to fetch stripe payment intents: {e}")
    return convert_completed_stripe_charges_to_payments(stripe_charges)
