from dataclasses import dataclass
import csv
from typing import List


@dataclass
class Accounting:
    article: str
    account: int

    @classmethod
    def parse_row(cls, row: dict):
        return cls(row["article"], int(row["account"]))

    @classmethod
    def parse_csv(cls, filename) -> List["Accounting"]:
        with open(filename, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            accounting = [cls.parse_row(row) for row in reader]
        return accounting


@dataclass
class Account:
    is_active: bool
    account: int
    name: str
    vat_code: str
    is_cost_center_allowed: bool
    is_project_allowed: bool
    allow_transaction_text: bool
    is_blocked_for_manual_booking: bool

    @classmethod
    def parse_row(cls, row: dict):
        return cls(
            bool(row["IsActive"]),
            int(row["AccountNumber"]),
            row["AccountName"],
            row["VatCodeAndPercent"],
            bool(row["IsCostCenterAllowed"]),
            bool(row["IsProjectAllowed"]),
            bool(row["AllowTransactionText"]),
            bool(row["IsBlockedForManualBooking"])
        )

    @classmethod
    def parse_csv(cls, filename) -> List["Account"]:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            accounts = [cls.parse_row(row) for row in reader]
        return accounts
@dataclass
class MonthlyTransactions:
    period: str
    amount_debit: float
    amount_credit:float
    account: int
    cost_center: int

    @classmethod
    def parse_row(cls,row: dict):
        return cls(
            str(row["Period"]),
            float(row["AmountDebit"]),
            float(row["AmountCredit"]),
            int(row["Account"]),
            int(row["CostCenter"])
        )
    @classmethod
    def parse_csv(cls,filename) -> List["MonthlyTransactions"]:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f,delimiter=' ')
            accounts = [cls.parse_row(row)for row in reader]
        return accounts            

