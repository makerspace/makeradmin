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
    diff_transactions_and_completed_payments,
    add_accounting_to_transactions,
)
from shop.accounting.sie_file import write_to_sie_file
from shop.accounting.verification import create_verificatons


def export_accounting() -> None:  # TODO input is two dates, filename?
    completed_payments = None  # TODO a different PR

    # TODO query for transactions
    transactions = None

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        raise InternalServerError(f"Transactions and completed payments do not match, {diff}")

    transactions_with_accounting = add_accounting_to_transactions(transactions, completed_payments)
    verifications = create_verificatons(transactions_with_accounting, completed_payments)
    write_to_sie_file(verifications)  # TODO probably some file name input
