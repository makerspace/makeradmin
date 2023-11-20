from argparse import ArgumentParser
from datetime import datetime
from dataclasses import dataclass, field
from typing import List
import csv
import pprint
import re


@dataclass
class StripeTransaction:
    dt: datetime
    id: int
    gross: float
    net: float
    fee: float
    what: str
    makeradmin_transaction_id: int = field(init=False)

    def __post_init__(self):
        self.makeradmin_transaction_id = self.get_makeradmin_transaction_id()

    @classmethod
    def parse_row(cls, row: dict):
        id = row["balance_transaction_id"]
        dt = datetime.strptime(row["created_utc"], "%Y-%m-%d %H:%M:%S")
        gross = float(row["gross"])
        net = float(row["net"])
        fee = float(row["fee"])
        what = row["description"]
        return cls(dt, id, gross, net, fee, what)

    def get_makeradmin_transaction_id(self) -> int:
        m = re.search(r'id (\d+)$', self.what)
        return int(m.group(1))

    @classmethod
    def parse_csv(cls, filename: str) -> List["StripeTransaction"]:
        with open(filename, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            transactions = [cls.parse_row(row) for row in reader if row["reporting_category"] == "charge"]
        return transactions


def main():
    parser = ArgumentParser()
    parser.add_argument("filename", help="CSV file from Stripe export")
    args = parser.parse_args()
    filename = args.filename
    transactions = StripeTransaction.parse_csv(filename)

    pprint.pprint(transactions)

    print(transactions[-1].get_makeradmin_transaction_id())


if __name__ == "__main__":
    main()
