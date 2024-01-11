from datetime import datetime
from logging import getLogger
from typing import Dict, List, Optional, Tuple

from membership.models import Member
from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import (
    AccountingEntryType,
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.sie_file import get_sie_string
from shop.accounting.verification import create_verificatons
from shop.models import (
    Product,
    ProductAccountsCostCenters,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostcenter,
)
from shop.stripe_payment_intent import (
    CompletedPayment,
    convert_completed_stripe_intents_to_payments,
    get_stripe_payment_intents,
)

logger = getLogger("makeradmin")


def transaction_fees_to_transaction_with_accounting(
    completed_payments: Dict[int, CompletedPayment],
) -> List[TransactionWithAccounting]:
    amounts: List[TransactionWithAccounting] = []
    for payment in completed_payments.values():
        amounts.append(
            TransactionWithAccounting(
                transaction_id=payment.transaction_id,
                product_id=None,
                amount=payment.fee,
                date=payment.created,
                account="6573",
                cost_center="Föreningsgemensamt",
                type=AccountingEntryType.DEBIT,
            )
        )
    return amounts


def export_accounting(start_date: datetime, end_date: datetime, filepath: str, signer: Member) -> str:
    logger.info(f"Exporting accounting from {start_date} to {end_date} with signer {signer.member_number}")
    stripe_payment_intents = get_stripe_payment_intents(start_date, end_date)
    completed_payments = convert_completed_stripe_intents_to_payments(stripe_payment_intents)
    transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        logger.warning(f"Transactions and completed payments do not match, {diff}")
        raise InternalServerError(f"Transactions and completed payments do not match, {diff}")

    transactions_with_accounting, leftover_amounts = split_transactions_over_accounts(transactions, completed_payments)
    if len(leftover_amounts) > 0:
        raise InternalServerError(
            f"Leftover amounts, {leftover_amounts}, currently not supporting all fractions for bookkeeping"
        )
    transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)
    transactions_with_accounting.extend(transaction_fees)
    verifications = create_verificatons(transactions_with_accounting)
    return get_sie_string(verifications, start_date, end_date, f"{signer.firstname} {signer.lastname}")
