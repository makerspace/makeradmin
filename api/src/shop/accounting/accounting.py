from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
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
    product_id: int | None
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


class RoundingErrorSource(Enum):
    FEE_SPLIT = "fee_split"  # From splitting the fee over the transaction contents
    TRANSACTION_SPLIT = (
        "transaction_split"  # From splitting the transaction over the different accounts and cost centers
    )


@dataclass(frozen=True)
class RoundingError:
    transaction_id: int
    amount: Decimal
    type: AccountingEntryType
    source: RoundingErrorSource
    date: datetime


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


def split_transaction_fee_over_transaction_contents(
    transaction: Transaction, fee: Decimal
) -> Tuple[Dict[int, Decimal], Decimal]:
    split_fees: Dict[int, Decimal] = {}
    rounding_error = fee
    for content in transaction.contents:
        adjusted_fee = round(Decimal(content.amount / transaction.amount) * fee, 2)
        split_fees[content.id] = adjusted_fee
        rounding_error -= adjusted_fee

    values = list(split_fees.values())
    max_key = list(split_fees.keys())[values.index(max(values))]
    split_fees[max_key] += rounding_error
    return split_fees, rounding_error


def split_transactions_over_accounts(
    transactions: List[Transaction], completed_payments: Dict[int, CompletedPayment]
) -> Tuple[List[TransactionWithAccounting], List[RoundingError]]:
    product_to_accounting = ProductToAccountCostCenter()
    transactions_with_accounting: List[TransactionWithAccounting] = []
    rounding_errors: List[RoundingError] = []

    for transaction in transactions:
        split_fees, rounding_error = split_transaction_fee_over_transaction_contents(
            transaction, completed_payments[transaction.id].fee
        )
        if rounding_error != Decimal("0.00"):
            rounding_error_obj = RoundingError(
                transaction.id,
                rounding_error,
                AccountingEntryType.DEBIT,
                RoundingErrorSource.FEE_SPLIT,
                transaction.created_at,
            )
            rounding_errors.append(rounding_error_obj)

        for content in transaction.contents:
            product_accounting = product_to_accounting.get_account_cost_center(content.product_id)
            if not product_accounting:
                raise InternalServerError(f"Product with id {content.product_id} has no accounting information")

            amounts_added: Dict[AccountingEntryType, Decimal] = {type: Decimal(0) for type in AccountingEntryType}
            adjusted_transaction_content_amounts: Dict[AccountingEntryType, Decimal] = {
                AccountingEntryType.CREDIT: Decimal(content.amount),
                AccountingEntryType.DEBIT: Decimal(content.amount) - split_fees[content.id],
            }

            index_to_add_leftover_amount = (-1, Decimal("-1"))
            for accounting in product_accounting:
                amount_to_add = adjusted_transaction_content_amounts[accounting.type] * (
                    accounting.fraction * Decimal("0.01")
                )  # Multiply with 0.01 instead of division by 100
                amount_to_add = Decimal(round(amount_to_add, 2))

                amounts_added[accounting.type] += amount_to_add

                logger.info(f"Accounting: {accounting}")
                logger.info(f"Amount to add: {amount_to_add}")
                logger.info(f"Amounts added: {amounts_added}")
                logger.info(f"Entry type: {accounting.type}")

                transacion_acc = TransactionWithAccounting(
                    transaction_id=transaction.id,
                    product_id=content.product_id,
                    amount=amount_to_add,
                    date=transaction.created_at,
                    account=accounting.account,
                    cost_center=accounting.cost_center,
                    type=accounting.type,
                )
                logger.info(f"Transaction with accounting: {transacion_acc}")
                transactions_with_accounting.append(transacion_acc)

                if accounting.type == AccountingEntryType.DEBIT and amount_to_add > index_to_add_leftover_amount[1]:
                    logger.info("*** update")
                    index_to_add_leftover_amount = (len(transactions_with_accounting) - 1, amount_to_add)

            for entry_type, amount_added in amounts_added.items():
                leftover_amount = adjusted_transaction_content_amounts[entry_type] - amount_added
                if leftover_amount != 0:
                    logger.info(f"Leftover amount: {leftover_amount}")
                    logger.info(f"Amount added: {amount_added}")
                    logger.info(f"Entry type: {entry_type}")
                    logger.info(f"Index to add leftover amount: {index_to_add_leftover_amount}")
                    transactions_with_accounting[index_to_add_leftover_amount[0]].amount += leftover_amount
                    rounding_error_obj = RoundingError(
                        transaction.id,
                        leftover_amount,
                        entry_type,
                        RoundingErrorSource.TRANSACTION_SPLIT,
                        transaction.created_at,
                    )
                    rounding_errors.append(rounding_error_obj)

    logger.info(f"Transactions with accounting: {transactions_with_accounting}")
    return transactions_with_accounting, rounding_errors
