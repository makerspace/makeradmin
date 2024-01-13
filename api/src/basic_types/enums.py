from enum import Enum


class PriceLevel(Enum):
    Normal = "normal"
    LowIncomeDiscount = "low_income_discount"


class AccountingEntryType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"
