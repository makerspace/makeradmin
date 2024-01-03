from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from basic_types.enums import AccountingEntryType
from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import (
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.sie_file import write_to_sie_file
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


def transaction_fees_to_transaction_with_accounting(
    completed_payments: List[CompletedPayment],
) -> List[TransactionWithAccounting]:
    amounts: List[TransactionWithAccounting] = []
    for payment in completed_payments:
        amounts.append(
            TransactionWithAccounting(
                amount=payment.fee,
                date=payment.created,
                account="6573",
                cost_center="Föreningsgemensamt",
                type=AccountingEntryType.DEBIT,
            )
        )
    return amounts


def export_accounting() -> None:  # TODO input is two dates, filename?
    stripe_payment_intents = get_stripe_payment_intents(start_date, end_date)
    completed_payments = convert_completed_stripe_intents_to_payments(stripe_payment_intents)

    # TODO query for transactions including contents
    transactions = None

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        raise InternalServerError(f"Transactions and completed payments do not match, {diff}")

    transactions_with_accounting = split_transactions_over_accounts(transactions)
    transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)
    transactions_with_accounting.extend(transaction_fees)
    verifications = create_verificatons(transactions_with_accounting, completed_payments)
    write_to_sie_file(verifications)  # TODO probably some file name input
