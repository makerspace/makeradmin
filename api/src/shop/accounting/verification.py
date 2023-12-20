from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from itertools import groupby
from operator import itemgetter

from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import TransactionWithAccountAndCostCenter


@dataclass(frozen=True)
class Verification:
    month: str
    account_id: int
    cost_center_id: int
    transactions: List[TransactionWithAccountAndCostCenter]


def group_by_month_account_cost_center(data: List[TransactionWithAccountAndCostCenter]) -> List[Verification]:
    data.sort(key=lambda x: (x.month, x.account_id, x.cost_center_id))
    grouped_data = []

    for key, group in groupby(data, key=itemgetter("month", "account_id", "cost_center_id")):
        month, account_id, cost_center_id = key
        transactions = list(group)
        grouped_data.append(
            Verification(month=month, account_id=account_id, cost_center_id=cost_center_id, transactions=transactions)
        )

    return grouped_data


def create_verificatons(data: List[TransactionWithAccountAndCostCenter]) -> List[Verification]:
    verifications = group_by_month_account_cost_center(data)
    return verifications
