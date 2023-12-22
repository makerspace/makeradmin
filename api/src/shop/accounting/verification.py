from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal

from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import AmountPerAccountAndCostCenter


@dataclass(frozen=True)
class Verification:
    period: str
    amounts: List[AmountPerAccountAndCostCenter]


def group_amounts(amounts: List[AmountPerAccountAndCostCenter]) -> Dict[str, List[AmountPerAccountAndCostCenter]]:
    grouped_amounts: Dict[str, List[AmountPerAccountAndCostCenter]] = {}
    for amount in amounts:
        year_month = amount.date.strftime("%Y-%m")
        if year_month in grouped_amounts:
            grouped_amounts[year_month].append(amount)
        else:
            grouped_amounts[year_month] = [amount]
    return grouped_amounts


def create_verificatons(transactions_with_accounting: List[AmountPerAccountAndCostCenter]) -> List[Verification]:
    grouped_amounts = group_amounts(transactions_with_accounting)
    verifications: List[Verification] = []
    for period, group in grouped_amounts.items():
        amounts = list(group)
        verifications.append(
            Verification(
                period=period,
                amounts=amounts,
            )
        )
    return verifications
