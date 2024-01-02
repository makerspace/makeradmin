from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple

from basic_types.enums import AccountingEntryType
from service.db import db_session
from service.error import InternalServerError
from shop.models import (
    Product,
    ProductAccountsCostCenters,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostcenter,
)
from shop.stripe_payment_intent import CompletedPayment

logger = getLogger("makeradmin")


@dataclass()
class TransactionWithAccounting:
    amount: Decimal
    date: datetime
    account: str | None
    cost_center: str | None
    type: AccountingEntryType


@dataclass()
class AccountCostCenter:
    acccount: str | None
    cost_center: str | None
    fraction: Decimal
    type: AccountingEntryType


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

            fraction_sums = Dict(AccountingEntryType, Decimal)
            fraction_sums[AccountingEntryType.CREDIT] = Decimal(0)
            fraction_sums[AccountingEntryType.DEBIT] = Decimal(0)
            account_cost_centers: List[AccountCostCenter] = []
            for product_info in product_accounting:
                if product_info.account.acccount is None and product_info.cost_center.cost_center is None:
                    raise InternalServerError(
                        f"Product {product.id} has accounting with both account and cost center as none"
                    )

                fraction_sums[product_info.account.type] += product_info.fraction
                account_cost_centers.append(
                    AccountCostCenter(
                        product_info.account.account,
                        product_info.cost_center.cost_center,
                        product_info.fraction,
                        product_info.account.type,
                    )
                )

            for key in fraction_sums:
                if fraction_sums[key] != Decimal(1):
                    raise InternalServerError(
                        f"Product {product.id} has accounting type {key} with fraction not adding up to 1"
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


def split_transactions_over_accounts(transactions: List[Transaction]) -> List[TransactionWithAccounting]:
    product_to_accounting = ProductToAccountCostCenter()
    transactions_with_accounting: List[TransactionWithAccounting] = []

    for transaction in transactions:
        logger.info(f"transaction: {transaction}")
        for product in transaction.contents:
            logger.info(f"product: {product}")
            product_accounting = product_to_accounting.get_account_cost_center(product.id)
            logger.info(f"product_accounting: {product_accounting}")
            for accounting in product_accounting:
                amount_to_add = accounting.fraction * transaction.amount  # TODO rounding errors?
                transactions_with_accounting.append(
                    TransactionWithAccounting(
                        amount=amount_to_add,
                        date=transaction.created_at,
                        account=accounting.acccount,
                        cost_center=accounting.cost_center,
                        type=accounting.type,
                    )
                )
    return transactions_with_accounting
