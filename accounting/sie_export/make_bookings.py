from collections import defaultdict
from typing import Dict, Tuple
from datetime import datetime
from argparse import ArgumentParser

from accounting import MonthlyTransactions


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


def main():
    parser = ArgumentParser()
    parser.add_argument("--signer", help="Who generated the file", required=True)
    parser.add_argument("--financial-year", type=int, required=True, help="The financial year of the bookings")
    parser.add_argument("--output", "-o", default=None, help="The output file where to save the export")
    parser.add_argument("--monthly-csv", required=True, help="csv for monthly transactions")
    args = parser.parse_args()

    monthly_transactions = MonthlyTransactions.parse_csv(args.monthly_csv)

    transaction_by_period = defaultdict(list)
    for transaction in monthly_transactions:
        transaction_by_period[transaction.period].append(transaction)

    file_str: str = ""
    file_str += get_header(args.signer, args.financial_year) + "\n"

    verfication_number = 1
    for period, transactions in transaction_by_period.items():
        period_date = datetime.strptime(period, "%Y-%m")
        date_str = date_format(period_date)
        month = period_date.strftime("%B")
        year = period_date.strftime("%Y")

        file_str += f'#VER B {verfication_number} {date_str} "{month} {year}"\n{{\n'

        for transaction in transactions:
            description = f"{transaction.period}"
            amount = transaction.amount_debit if (transaction.amount_debit == 0) else -transaction.amount_credit

            file_str += (
                transaction_string(
                    transaction.account,
                    transaction.cost_center,
                    transaction.amount_credit - transaction.amount_debit,
                    date_str,
                    description,
                )
                + "\n"
            )

            file_str += (
                transaction_string(
                    transaction.account,
                    transaction.cost_center,
                    transaction.amount_credit - transaction.amount_debit,
                    date_str,
                    description,
                )
                + "\n"
            )

        verfication_number += 1
        file_str += "}\n"

    if args.output:
        with open(args.output, mode="w", encoding="cp437") as f:
            f.write(file_str)
    else:
        print(file_str)


if __name__ == "__main__":
    main()
