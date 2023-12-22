from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from service.db import db_session
from service.error import InternalServerError
from shop.models import (
    Product,
    TransactionAccount,
    TransactionCostcenter,
    ProductAccountsCostCenters,
    Transaction,
    TransactionContent,
)
from shop.stripe_payment_intent import CompletedPayment
from shop.accounting.accounting import (
    AmountPerAccountAndCostCenter,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.sie_file import write_to_sie_file
from shop.accounting.verification import create_verificatons


def transaction_fees_to_transaction_with_accounting(
    completed_payments: List[CompletedPayment],
) -> List[AmountPerAccountAndCostCenter]:
    amounts: List[AmountPerAccountAndCostCenter] = []
    for payment in completed_payments:
        amounts.append(
            AmountPerAccountAndCostCenter(
                amount=payment.fee,
                date=payment.created,
                account="6573",
                cost_center="Föreningsgemensamt",
            )
        )
    return amounts


def export_accounting() -> None:  # TODO input is two dates, filename?
    completed_payments = None  # TODO a different PR

    # TODO query for transactions
    transactions = None

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        raise InternalServerError(f"Transactions and completed payments do not match, {diff}")

    transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)
    transactions_with_accounting.extend(transaction_fees)
    transactions_with_accounting = split_transactions_over_accounts(transactions, completed_payments)
    verifications = create_verificatons(transactions_with_accounting, completed_payments)
    write_to_sie_file(verifications)  # TODO probably some file name input
