from enum import Enum


class PriceLevel(Enum):
    Normal = "normal"
    LowIncomeDiscount = "low_income_discount"
    AWLDiscount = "awl_discount"


class AccountingEntryType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"
