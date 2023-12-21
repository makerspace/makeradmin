from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal

from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import AmountPerAccountAndCostCenter
from shop.stripe_payment_intent import CompletedPayment


@dataclass(frozen=True)
class Verification:
    period: str
    total_transaction_fee: Decimal
    total_amount_ex_fee: Decimal
    amounts: List[AmountPerAccountAndCostCenter]


def group_transaction_fees(completed_payments: List[CompletedPayment]) -> Dict[str, Decimal]:
    transaction_fees: Dict[str, Decimal] = {}
    for payment in completed_payments:
        year_month = payment.created.strftime("%Y-%m")
        if year_month in transaction_fees:
            transaction_fees[year_month] += payment.fee
        else:
            transaction_fees[year_month] = payment.fee
    return transaction_fees


def group_amounts(amounts: List[AmountPerAccountAndCostCenter]) -> Dict[str, List[AmountPerAccountAndCostCenter]]:
    grouped_amounts: Dict[str, List[AmountPerAccountAndCostCenter]] = {}
    for amount in amounts:
        year_month = amount.date.strftime("%Y-%m")
        if year_month in grouped_amounts:
            grouped_amounts[year_month].append(amount)
        else:
            grouped_amounts[year_month] = [amount]
    return grouped_amounts


def create_verificatons(
    transactions_with_accounting: List[AmountPerAccountAndCostCenter], completed_payments: List[CompletedPayment]
) -> List[Verification]:
    grouped_fees = group_transaction_fees(completed_payments)
    grouped_amounts = group_amounts(transactions_with_accounting)
    verifications: List[Verification] = []
    for period, group in grouped_amounts.items():
        amounts = list(group)
        if period not in grouped_fees:
            raise InternalServerError(f"Missing transaction fee for period {period}")
        total_transaction_fee = grouped_fees[period]
        total_amount_ex_fee = sum([amount.amount for amount in amounts]) - total_transaction_fee
        verifications.append(
            Verification(
                period=period,
                total_transaction_fee=total_transaction_fee,
                total_amount_ex_fee=total_amount_ex_fee,
                amounts=amounts,
            )
        )
    return verifications
