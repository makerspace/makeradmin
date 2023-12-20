from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from itertools import groupby
from operator import itemgetter

from shop.accounting.verification import Verification


def convert_to_sie_format(verifications: List[Verification]) -> List[str]:
    sie_content = []

    for verification in verifications:
        sie_content.append(f"#VER {verification.month} {verification.account_id} {verification.cost_center_id}")

        for transaction in verification.transactions:
            sie_content.append(
                f"#TRANS {transaction.created_at.strftime('%Y%m%d')} {transaction.account_id} {float(transaction.amount)}"
            )

    return sie_content


def write_to_sie_file(verifications: List[Verification], file_name: str) -> None:
    sie_content = convert_to_sie_format(verifications)

    with open(file_name, "w") as file:
        file.write("\n".join(sie_content))
