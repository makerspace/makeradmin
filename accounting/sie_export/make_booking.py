from typing import Dict, Tuple
from transactions import Purchase
from stripe_transactions import StripeTransaction
from argparse import ArgumentParser
from datetime import datetime
from accounting import account_name_lookup, accounts
import sys

HEADER_TEMPLATE = '''
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
'''


def date_format(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def get_header(signer: str, financial_year: int):
    return HEADER_TEMPLATE.format(
        date=date_format(datetime.now()),
        signer=signer,
        date_start=date_format(datetime(financial_year, 1, 1)),
        date_end=date_format(datetime(financial_year, 12, 31))
    )


def transaction_string(account, sum, date, description) -> str:
    return f'#TRANS {account} {{}} {sum} {date} "{description}"'


def main():
    parser = ArgumentParser()
    parser.add_argument("--signer", help="Who generated the file", required=True)
    parser.add_argument("--makeradmin-tsv", nargs="?", required=True,
                        help=".tsv file exported using the export_transactions.sh script on the Makeradmin server")
    parser.add_argument("--stripe-csv", required=True,
                        nargs="?", help=".csv file exported from Stripe")
    parser.add_argument("--output", "-o", default=None, help="The output file where to save the export")
    parser.add_argument("--no-summary", action="store_true", help="Do not print a summary of the accounts")
    parser.add_argument("--financial-year", type=int, required=True,
                        help="The financial year of the bookings")
    args = parser.parse_args()

    purchases = Purchase.parse_csv(args.makeradmin_tsv)
    stripe_transactions = StripeTransaction.parse_csv(args.stripe_csv)

    ma_transaction_ids = set(t.id for t in purchases)
    stripe_transaction_ids = set(t.get_makeradmin_transaction_id() for t in stripe_transactions)

    # Check that we have exactly the same transactions in Makeradmin and Stripe (very important)
    transaction_differences = ma_transaction_ids.symmetric_difference(stripe_transaction_ids)
    if len(transaction_differences):
        for id in transaction_differences:
            if id in ma_transaction_ids:
                print(f"{id} is in makeradmin, but not in stripe")
            else:
                print(f"{id} is in stripe, but not in makeradmin")
        raise ValueError("There is a difference in transaction ID:s - Should not happen")

    transactions: Dict[int, Tuple[Purchase, StripeTransaction]] = dict()
    for transaction_id in ma_transaction_ids:
        for p in purchases:
            if p.id == transaction_id:
                ma_transaction = p
                break

        for p2 in stripe_transactions:
            if p2.makeradmin_transaction_id == transaction_id:
                stripe_transaction = p2
                break

        transactions[transaction_id] = (ma_transaction, stripe_transaction)

    if not all(t.dt.year == args.financial_year for t in purchases):
        print(f"Error: There are transactions that do not belong to the financial year {args.financial_year}.",
              file=sys.stderr, flush=True)

    account_sums = {account: 0 for account, name in account_name_lookup.items()}

    # Create string to write to file
    file_str: str = ""
    file_str += get_header(args.signer, args.financial_year) + "\n"

    # for account in accounts:
    #     r = f"#KONTO {account.account} \"{account.name}\"\n"
    #     file_str += r

    # Create all transactions
    verfication_number = 1
    for transaction_id in sorted(ma_transaction_ids):
        ma_trans, stripe_trans = transactions[transaction_id]
        datestr = date_format(ma_trans.dt)
        file_str += "\n"
        file_str += f'#VER B {verfication_number} {datestr} "Makeradmin order #{ma_trans.id}"\n'
        file_str += "{\n"
        for art in ma_trans.art:
            account_sums[art.account] += art.amount
            file_str += transaction_string(art.account, -art.amount, datestr, art.what) + "\n"
        file_str += transaction_string(1933, stripe_trans.net, datestr, f"Stripe {stripe_trans.id}") + "\n"
        account_sums[1933] -= stripe_trans.net
        file_str += transaction_string(6573, stripe_trans.fee, datestr, f"Stripe {stripe_trans.id}") + "\n"
        account_sums[6573] -= stripe_trans.fee
        file_str += "}\n"

        art_sum = sum([art.amount for art in ma_trans.art])
        if art_sum != stripe_trans.gross:
            print(f"Makeradmin sum {art_sum} does not match stripe gross amount {stripe_trans.gross}")
            print(f"For makeradmin transaction {ma_trans.id} and stripe id {transaction_id}")
            print(ma_trans.art)
            raise ValueError(f"Should not happen")

        verfication_number += 1

    if not args.no_summary:
        print(f"Account summary for {args.financial_year}:")
        for account_id, account_sum in account_sums.items():
            if account_sum != 0:
                print(f"{account_id:4d}: {account_sum:8.1f} kr ({account_name_lookup[account_id]})")

    if args.output is not None:
        with open(args.output, mode="w", encoding="cp437") as f:
            f.write(file_str)


if __name__ == "__main__":
    main()
