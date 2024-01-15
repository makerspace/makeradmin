from datetime import datetime
from logging import getLogger
from typing import Dict, List, Tuple

from basic_types.enums import AccountingEntryType
from basic_types.time_period import TimePeriod
from membership.models import Member
from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import (
    RoundingError,
    RoundingErrorSource,
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.sie_file import get_sie_string
from shop.accounting.verification import create_verificatons
from shop.models import (
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
)
from shop.stripe_payment_intent import CompletedPayment, get_completed_payments_from_stripe

logger = getLogger("makeradmin")


def transaction_fees_to_transaction_with_accounting(
    completed_payments: Dict[int, CompletedPayment],
) -> List[TransactionWithAccounting]:
    amounts: List[TransactionWithAccounting] = []
    account = TransactionAccount(account="6573", description="6573", id=0, display_order=1)
    cost_center = TransactionCostCenter(
        cost_center="Föreningsgemensamt", description="Föreningsgemensamt", id=0, display_order=1
    )
    for payment in completed_payments.values():
        amounts.append(
            TransactionWithAccounting(
                transaction_id=payment.transaction_id,
                product_id=None,
                amount=payment.fee,
                date=payment.created,
                account=account,
                cost_center=cost_center,
                type=AccountingEntryType.DEBIT,
            )
        )
    return amounts


def export_accounting(start_date: datetime, end_date: datetime, group_by_period: TimePeriod, member_id: int) -> str:
    signer = db_session.query(Member).filter(Member.member_id == member_id).one_or_none()
    if signer is None:
        raise InternalServerError(f"Member with id {member_id} not found")
    logger.info(f"Exporting accounting from {start_date} to {end_date} with signer {signer.member_number}")
    completed_payments = get_completed_payments_from_stripe(start_date, end_date)
    transactions = (
        db_session.query(Transaction)
        .filter(
            Transaction.created_at >= start_date,
            Transaction.created_at < end_date,
            Transaction.status == Transaction.COMPLETED,
        )
        .outerjoin(TransactionContent)
        .all()
    )

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        raise InternalServerError(f"Transactions and completed payments do not match, {diff}")

    transactions_with_accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)
    logger.info(f"Roundings errors from split: {rounding_errors}")

    transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)
    transactions_with_accounting.extend(transaction_fees)

    verifications = create_verificatons(transactions_with_accounting, group_by_period)
    logger.info(f"Verifications: {verifications}")

    return get_sie_string(verifications, start_date, end_date, f"{signer.firstname} {signer.lastname}")
