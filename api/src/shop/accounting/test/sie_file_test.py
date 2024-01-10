from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase

from basic_types.enums import AccountingEntryType
from shop.accounting.sie_file import (
    convert_to_sie_format,
    get_sie_string,
    transaction_string,
    verification_string,
)
from shop.accounting.verification import Verification

logger = getLogger("makeradmin")


class SieFileTest(TestCase):
    def test_verification_string(self) -> None:
        period = datetime(
            2023,
            1,
            2,
        ).strftime("%Y-%m")
        verification = Verification(period, {}, {}, "B")
        verification_str = verification_string(verification, 1)

        assert f'#VER B 1 20230101 "MakerAdmin"' == verification_str

    def test_transaction_string(self) -> None:
        account = "account"
        cost_center = "cost center"
        sum = Decimal("100.0")
        period = datetime(
            2023,
            1,
            2,
        ).strftime("%Y-%m")
        description = "test"
        transaction_str = transaction_string(account, cost_center, sum, period, description)

        assert f'#TRANS account {{1 "cost center"}} 100.0 20230101 "test"' == transaction_str

    def test_transaction_string_cc_none(self) -> None:
        account = "account"
        cost_center = None
        sum = Decimal("100.0")
        period = datetime(
            2023,
            1,
            2,
        ).strftime("%Y-%m")
        description = "test"
        transaction_str = transaction_string(account, cost_center, sum, period, description)

        assert f'#TRANS account {{}} 100.0 20230101 "test"' == transaction_str


class SieFileWithVerificationTest(TestCase):
    number_of_verifications = 2
    number_of_transactions = 3

    def setUp(self) -> None:
        self.verifications: List[Verification] = []

        for i in range(1, self.number_of_verifications + 1):
            period = datetime(
                2023,
                i,
                i + 3,
            ).strftime("%Y-%m")
            amounts: Dict[Tuple[str | None, str | None], Decimal] = {}
            types: Dict[Tuple[str | None, str | None], AccountingEntryType] = {}

            for j in range(1, self.number_of_transactions + 1):
                account = f"account{j}"
                cost_center = f"cost_center{j}"
                if j % 2 == 0:
                    entry_type = AccountingEntryType.DEBIT
                    amount = Decimal("1000") + Decimal(f"{i * j + j}")
                else:
                    entry_type = AccountingEntryType.CREDIT
                    amount = Decimal(f"{i * j + j}")
                amounts[(account, cost_center)] = amount
                types[(account, cost_center)] = entry_type

            verification = Verification(period, amounts, types, "B")
            self.verifications.append(verification)

    def test_convert_to_sie_format(self) -> None:
        sie_rows = convert_to_sie_format(self.verifications)

        for i in range(1, self.number_of_verifications + 1):
            verification_row = sie_rows.pop(0)
            assert verification_row.startswith(f'#VER B {i} 2023{i:02d}01 "MakerAdmin"')
            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "{"

            for j in range(1, self.number_of_transactions + 1):
                transaction_row = sie_rows.pop(0)
                if j % 2 == 0:
                    assert transaction_row.startswith(
                        f'#TRANS account{j} {{1 "cost_center{j}"}} -{Decimal("1000") + Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )
                else:
                    assert transaction_row.startswith(
                        f'#TRANS account{j} {{1 "cost_center{j}"}} {Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )

            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "}"

        assert len(sie_rows) == 0

    def test_get_sie_string(self) -> None:
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        signer = "Maker Makerson"

        sie_str = get_sie_string(self.verifications, start_date, end_date, signer)

        sie_rows = sie_str.split("\n")

        in_header = True
        while in_header == True:
            row = sie_rows.pop(0)

            if row.startswith("#GEN"):
                assert datetime.now().strftime("%Y%m%d") in row
                assert signer in row

            if row.startswith("#DIM"):
                assert "Kostnadställe" in row
                in_header = False

        for i in range(1, self.number_of_verifications + 1):
            verification_row = sie_rows.pop(0)
            assert verification_row.startswith(f'#VER B {i} 2023{i:02d}01 "MakerAdmin"')
            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "{"

            for j in range(1, self.number_of_transactions + 1):
                transaction_row = sie_rows.pop(0)

                if j % 2 == 0:
                    assert transaction_row.startswith(
                        f'#TRANS account{j} {{1 "cost_center{j}"}} -{Decimal("1000") + Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )
                else:
                    assert transaction_row.startswith(
                        f'#TRANS account{j} {{1 "cost_center{j}"}} {Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )

            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "}"

        assert len(sie_rows) == 0
