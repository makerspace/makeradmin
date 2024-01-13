from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Tuple

from basic_types.enums import AccountingEntryType
from service.db import db_session
from service.error import InternalServerError
from shop.models import (
    Product,
    ProductAccountsCostCenters,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
)
from shop.stripe_payment_intent import CompletedPayment

logger = getLogger("makeradmin")


@dataclass()
class TransactionWithAccounting:
    transaction_id: int
    product_id: int
    amount: Decimal
    date: datetime
    account: TransactionAccount | None
    cost_center: TransactionCostCenter | None
    type: AccountingEntryType


@dataclass(frozen=True)
class AccountCostCenter:
    account: TransactionAccount | None
    cost_center: TransactionCostCenter | None
    fraction: int
    type: AccountingEntryType


class ProductToAccountCostCenter:
    def __init__(self) -> None:
        self.product_to_account_cost_center: Dict[int, List[AccountCostCenter]] = {}

        products = db_session.query(Product).all()
        for product in products:
            product_accounting = (
                db_session.query(ProductAccountsCostCenters)
                .outerjoin(TransactionAccount, ProductAccountsCostCenters.account)
                .outerjoin(TransactionCostCenter, ProductAccountsCostCenters.cost_center)
                .filter(ProductAccountsCostCenters.product_id == product.id)
                .all()
            )

            entry_type_found = {entry_type: False for entry_type in AccountingEntryType}
            fraction_sums: Dict[AccountingEntryType, int] = {}
            fraction_sums[AccountingEntryType.CREDIT] = 0
            fraction_sums[AccountingEntryType.DEBIT] = 0
            account_cost_centers: List[AccountCostCenter] = []
            for product_info in product_accounting:
                account = product_info.account if product_info.account is not None else None
                cost_center = product_info.cost_center if product_info.cost_center is not None else None
                if account is None and cost_center is None:
                    raise InternalServerError(
                        f"Product with id {product.id} has accounting with both account and cost center as None. At least one must be set to a value."
                    )
                if product_info.fraction <= 0 or product_info.fraction > 100:
                    raise InternalServerError(
                        f"Product with id {product.id} has accounting with id {product_info.id} with fraction {product_info.fraction} not in range [1, 100]"
                    )

                accounting_type = AccountingEntryType(product_info.type)
                entry_type_found[accounting_type] = True
                fraction_sums[accounting_type] += product_info.fraction
                account_cost_centers.append(
                    AccountCostCenter(
                        account,
                        cost_center,
                        product_info.fraction,
                        accounting_type,
                    )
                )

            for key in fraction_sums:
                if not entry_type_found[key]:
                    raise InternalServerError(
                        f"Product with id {product.id} named {product.name} has no accounting information for {key.value}"
                    )
                if fraction_sums[key] != 100:
                    raise InternalServerError(
                        f"Product with id {product.id} named {product.name} has accounting type {key.value} "
                        + f"with fraction weights not adding up to 100, was {fraction_sums[key]}",
                    )

            self.product_to_account_cost_center[product.id] = account_cost_centers

    def get_account_cost_center(self, product_id: int) -> List[AccountCostCenter]:
        return self.product_to_account_cost_center[product_id]


def diff_transactions_and_completed_payments(
    transactions: List[Transaction], completed_payments: Dict[int, CompletedPayment]
) -> List[Tuple[Transaction | None, CompletedPayment | None]]:
    unmatched_data: List[Tuple[Transaction | None, CompletedPayment]] = []
    completed_payments = completed_payments.copy()  # TODO improve this and remove pop

    for transaction in transactions:
        if transaction.status != Transaction.COMPLETED:
            continue
        if transaction.id not in completed_payments:
            unmatched_data.append((transaction, None))
            continue
        completed_payment = completed_payments.pop(transaction.id)
        if transaction.amount != float(completed_payment.amount) or transaction.id != completed_payment.transaction_id:
            unmatched_data.append((transaction, completed_payment))

    if len(completed_payments) > 0:
        logger.warning(f"Completed payments without matching transaction, {completed_payments}")
        for payment in completed_payments.values():
            unmatched_data.append((None, payment))

    return unmatched_data


def split_transaction_fee_over_transaction_contents(transaction: Transaction, fee: Decimal) -> Dict[int, Decimal]:
    split_fees: Dict[int, Decimal] = {}
    leftover_fee = fee
    for content in transaction.contents:
        adjusted_fee = round(Decimal(content.amount / transaction.amount) * fee, 2)
        split_fees[content.id] = adjusted_fee
        leftover_fee -= adjusted_fee
    split_fees[transaction.contents[0].id] += leftover_fee
    return split_fees


def split_transactions_over_accounts(
    transactions: List[Transaction], completed_payments: Dict[int, CompletedPayment]
) -> Tuple[List[TransactionWithAccounting], Dict[Tuple[int, int, AccountingEntryType], Decimal]]:
    product_to_accounting = ProductToAccountCostCenter()
    transactions_with_accounting: List[TransactionWithAccounting] = []
    leftover_amounts: Dict[Tuple[int, int, AccountingEntryType], Decimal] = {}

    for transaction in transactions:
        split_fees = split_transaction_fee_over_transaction_contents(
            transaction, completed_payments[transaction.id].fee
        )
        for content in transaction.contents:
            product_accounting = product_to_accounting.get_account_cost_center(content.product_id)

            amounts_added: Dict[AccountingEntryType, Decimal] = {type: Decimal(0) for type in AccountingEntryType}

            for accounting in product_accounting:
                adjusted_transaction_content_amount = (
                    Decimal(content.amount)
                    if accounting.type == AccountingEntryType.CREDIT
                    else Decimal(content.amount) - split_fees[content.id]
                )
                amount_to_add = adjusted_transaction_content_amount * (
                    accounting.fraction * Decimal("0.01")
                )  # Multiply with 0.01 instead of division by 100
                amount_to_add = Decimal(round(amount_to_add, 2))

                key = accounting.type
                amounts_added[key] += amount_to_add

                transactions_with_accounting.append(
                    TransactionWithAccounting(
                        transaction_id=transaction.id,
                        product_id=content.product_id,
                        amount=amount_to_add,
                        date=transaction.created_at,
                        account=accounting.account,
                        cost_center=accounting.cost_center,
                        type=accounting.type,
                    )
                )

            for entry_type, amount in amounts_added.items():
                adjusted_transaction_content_amount = (
                    Decimal(content.amount)
                    if entry_type == AccountingEntryType.CREDIT
                    else Decimal(content.amount) - split_fees[content.id]
                )
                if amount != adjusted_transaction_content_amount:
                    leftover_key: Tuple[int, int, AccountingEntryType] = (
                        transaction.id,
                        content.product_id,
                        entry_type,
                    )
                    leftover_amounts[leftover_key] = adjusted_transaction_content_amount - amount
    return transactions_with_accounting, leftover_amounts
