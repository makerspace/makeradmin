from datetime import datetime
from decimal import Decimal
from itertools import groupby
from operator import itemgetter
from typing import Dict, List, Optional, Tuple

from basic_types.enums import AccountingEntryType
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


def period_to_date_format(period: str) -> str:
    return datetime.strptime(period, "%Y-%m").strftime("%Y%m%d")


def date_format(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def get_header(signer: str, start_date: datetime, end_date: datetime):
    return HEADER_TEMPLATE.format(
        date=date_format(datetime.now()),
        signer=signer,
        date_start=date_format(start_date),
        date_end=date_format(end_date),
    )


def verification_string(verification: Verification, verfication_number: int) -> str:
    return f'#VER {verification.serie} {verfication_number} {period_to_date_format(verification.period)} "MakerAdmin"'


def transaction_string(account: str, cost_center: str | None, sum: Decimal, period: str, description: str) -> str:
    if account is None:
        raise ValueError("Account cannot be None for SIE export.")
    if cost_center is None:
        cc_string = f"{{}}"
    else:
        cc_string = f'{{1 "{cost_center}"}}'
    return f'#TRANS {account} {cc_string} {sum} {period_to_date_format(period)} "{description}"'


def convert_to_sie_format(verifications: List[Verification]) -> List[str]:
    sie_content = []
    verifications.sort(key=lambda verification: verification.period)

    for verfication_number, verification in enumerate(verifications):
        sie_content.append(verification_string(verification, verfication_number + 1))
        sie_content.append("{")

        for accounting_key, amount in verification.amounts.items():
            account = accounting_key[0]
            cost_center = accounting_key[1]
            if account is None:
                raise ValueError("Account cannot be None for SIE export.")
            sie_amount_adjusted = -amount if verification.types[accounting_key] == AccountingEntryType.DEBIT else amount
            sie_content.append(
                transaction_string(
                    account,
                    cost_center,
                    sie_amount_adjusted,
                    verification.period,
                    f"MakerAdmin period {verification.period}",
                )
            )
        sie_content.append("}")

    return sie_content


def get_sie_string(verifications: List[Verification], start_date: datetime, end_date: datetime, signer: str) -> str:
    sie_content = convert_to_sie_format(verifications)

    header = get_header(signer, start_date, end_date)

    return header + "\n".join(sie_content)
