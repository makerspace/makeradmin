from logging import getLogger
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

logger = getLogger("makeradmin")


@dataclass()
class AmountPerAccountAndCostCenter:
    amount: Decimal
    date: datetime
    account: str
    type: str  # TODO fix
    cost_center: str | None


@dataclass()
class AccountCostCenter:
    acccount: str
    cost_center: str | None
    type: str  # TODO fix this
    fraction: Decimal


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
                        product_info.fraction,
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


def split_transactions_over_accounts(transactions: List[Transaction]) -> List[AmountPerAccountAndCostCenter]:
    product_to_accounting = ProductToAccountCostCenter()
    transactions_with_accounting: Dict[Tuple[str, str], AmountPerAccountAndCostCenter] = []

    for transaction in transactions:
        logger.info(f"transaction: {transaction}")
        for product in transaction.contents:
            logger.info(f"product: {product}")
            product_accounting = product_to_accounting.get_account_cost_center(product.id)
            logger.info(f"product_accounting: {product_accounting}")
            for accounting in product_accounting:
                amount_to_add = accounting.fraction * transaction.amount  # TODO rounding errors?
                key = {accounting.acccount, accounting.cost_center}
                if key in transactions_with_accounting:
                    transactions_with_accounting[key].amount += amount_to_add
                else:
                    transactions_with_accounting[key] = AmountPerAccountAndCostCenter(
                        amount=amount_to_add,
                        date=transaction.created_at,
                        account=accounting.acccount,
                        cost_center=accounting.cost_center,
                    )

    return transactions_with_accounting.values()
