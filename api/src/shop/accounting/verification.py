from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import TransactionWithAccounting


@dataclass(frozen=True)
class Verification:
    period: str
    amounts: Dict[Tuple[str | None, str | None], Decimal]


def create_verificatons(
    transactions_with_accounting: List[TransactionWithAccounting],
) -> List[Verification]:
    verifications: Dict[str, Verification] = {}
    for transaction in transactions_with_accounting:
        year_month = transaction.date.strftime("%Y-%m")
        inner_key = (transaction.account, transaction.cost_center)
        if year_month in verifications:
            if inner_key in verifications[year_month].amounts:
                verifications[year_month].amounts[inner_key] += transaction.amount
            else:
                verifications[year_month].amounts[inner_key] = transaction.amount
        else:
            verifications[year_month] = Verification(year_month, {inner_key: transaction.amount})
    return list(verifications.values())
