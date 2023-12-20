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
from shop.accounting.sie_file import write_to_sie_file
from shop.accounting.verification import create_verificatons


@dataclass(frozen=True)
class TransactionWithAccountAndCostCenter:
    transaction_id: int
    amount: Decimal
    transaction_fee: Decimal
    date: datetime
    account: int
    cost_center: str


@dataclass()
class AccountCostCenter:
    acccount: int
    cost_center: str
    debit: Decimal
    credit: Decimal


class ProductToAccountCostCenter:
    def __init__(self) -> None:
        self.product_to_account_cost_center: Dict[int, List[AccountCostCenter]] = {}

        products = db_session.query(Product).all()
        for product in products:
            product_accounting = (
                db_session.query(ProductAccountsCostCenters, TransactionAccount, TransactionCostcenter)
                .join(TransactionAccount, ProductAccountsCostCenters.account)
                .join(TransactionCostcenter, ProductAccountsCostCenters.cost_center)
                .filter(ProductAccountsCostCenters.product_id == product.id)
                .all()
            )
            account_cost_centers: List[AccountCostCenter] = []
            for product_info in product_accounting:
                account_cost_centers.append(
                    AccountCostCenter(
                        product_info.account.account,
                        product_info.cost_center.cost_center,
                        product_info.debit,
                        product_info.credit,
                    )
                )

            self.product_to_account_cost_center[product.id] = account_cost_centers

    def get_account_cost_center(self, product_id: int) -> List[AccountCostCenter]:
        return self.product_to_account_cost_center[product_id]


def diff_transactions_and_completed_payments(
    transactions: List[Transaction], completed_payments: Dict[int, CompletedPayment]
) -> List[Tuple[Transaction | None, CompletedPayment]]:
    unmatched_data: List[Tuple[Transaction | None, CompletedPayment]] = []

    for transaction in transactions:
        if transaction.status != Transaction.COMPLETED:
            continue
        completed_payment = completed_payments.pop(transaction.id)
        if transaction.amount != completed_payment.amount or transaction.id != completed_payment.transaction_id:
            unmatched_data.append((transaction, completed_payment))

    if len(completed_payments) > 0:
        unmatched_data.append((None, completed_payments))

    return unmatched_data


def add_accounting_to_transactions(
    product_to_accounting: ProductToAccountCostCenter,
    transactions: List[Transaction],
    completed_payments: List[CompletedPayment],
) -> List[TransactionWithAccountAndCostCenter]:
    product_to_accounting = ProductToAccountCostCenter()

    # TODO query TransactionContent for products somewhere

    transactions_with_accounting: List[TransactionWithAccountAndCostCenter] = []
    for payment in completed_payments:
        pass  # TODO
    return transactions_with_accounting


def export_accounting() -> None:  # TODO input is two dates
    completed_payments = None  # TODO a different PR

    # TODO query for transactions
    transactions = None

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        raise InternalServerError(f"Transactions and completed payments do not match, {diff}")

    transactions_with_accounting = add_accounting_to_transactions(transactions, completed_payments)

    verifications = create_verificatons(transactions_with_accounting)  # TODO probably some group by input

    write_to_sie_file(verifications)  # TODO probably some file name input
