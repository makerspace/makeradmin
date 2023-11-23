from datetime import datetime
from dataclasses import dataclass, field
from typing import List
import csv
import pprint


@dataclass
class Article:
    dt: datetime
    id: int
    amount: float
    what: str
    account: int = field(init=False)

    def __post_init__(self):
        try:
            self.account = account_lookup[self.what]
        except KeyError as e:
            raise Exception(f"Could not find article '{self.what}' in the accounting lookup!") from e

    @classmethod
    def parse_row(cls, row: str):
        values = row.split("\t")
        id = int(values[1])
        dt = datetime.strptime(values[0], "%Y-%m-%d %H:%M:%S")
        amount = float(values[2])
        what = values[3].strip()
        return cls(dt, id, amount, what)


@dataclass
class Purchase:
    id: int
    art: List[Article]
    amount: float
    dt: datetime = field(init=False)

    def __init__(self, id: int):
        self.id = id
        self.art = []
        self.amount = 0.0

    def add(self, t: Article):
        self.art.append(t)
        self.amount += t.amount

    @property
    def dt(self) -> datetime:
        return self.art[0].dt

    @classmethod
    def parse_csv(self, filename: str) -> List["Purchase"]:
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()

        articles = []
        any_errors = False
        for row in lines[1:]:
            try:
                articles.append(Article.parse_row(row))
            except Exception as e:
                any_errors = True
                print(e)

        if any_errors:
            exit(1)

        ids = set()
        for t in articles:
            ids.add(t.id)

        purchases = []
        for id in ids:
            purchase = Purchase(id)
            for t in articles:
                if t.id == id:
                    purchase.add(t)
            purchases.append(purchase)

        return purchases


def main():
    filename = "transactions_2021.tsv"
    purchases = Purchase.parse_csv(filename)
    pprint.pprint(purchases)


if __name__ == "__main__":
    main()
