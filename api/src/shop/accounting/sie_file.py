from datetime import datetime
from decimal import Decimal
from itertools import groupby
from operator import itemgetter
from typing import Dict, List, Optional, Tuple

from membership.models import Member
from shop.accounting.verification import Verification

HEADER_TEMPLATE = """
#FLAGGA 0

#PROGRAM "MakerAdmin Booking" 1.0
#FORMAT PC8
#GEN {date} "{signer}"
#SIETYP 4
#ORGNR 802467-7026
#FNAMN "STOCKHOLM MAKERSPACE"
#RAR 0 {date_start} {date_end}
#KPTYP EUBAS97
#VALUTA SEK
#DIM 1 "Kostnadställe"
"""


def date_format(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def get_header(signer: str, financial_year: int):
    return HEADER_TEMPLATE.format(
        date=date_format(datetime.now()),
        signer=signer,
        date_start=date_format(datetime(financial_year, 1, 1)),
        date_end=date_format(datetime(financial_year, 12, 31)),
    )


def transaction_string(account, cost_center, sum, date, description) -> str:
    return f'#TRANS {account} {{"1" "{cost_center}"}} {sum} {date} "{description}"'


def convert_to_sie_format(verifications: List[Verification]) -> List[str]:
    sie_content = []

    for verification in verifications:
        sie_content.append(f"#VER {verification.month} {verification.account_id} {verification.cost_center_id}")

        for transaction in verification.transactions:
            sie_content.append(
                f"#TRANS {transaction.created_at.strftime('%Y%m%d')} {transaction.account_id} {float(transaction.amount)}"
            )

    return sie_content


def write_to_sie_file(verifications: List[Verification], file_name: str, signer: Member) -> None:
    sie_content = convert_to_sie_format(verifications)

    header = get_header(signer, year)

    with open(file_name, "w") as file:
        file.write("\n".join(sie_content))
