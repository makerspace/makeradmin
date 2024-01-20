import random
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Tuple
from unittest import TestCase

import core
import membership
import pytest
import shop
from basic_types.enums import AccountingEntryType
from service.db import db_session
from shop.accounting.accounting import TransactionAccount, TransactionCostCenter
from shop.accounting.sie_file import (
    convert_to_sie_format,
    get_account_header,
    get_cost_center_header,
    get_sie_string,
    transaction_string,
    verification_string,
)
from shop.accounting.verification import Verification
from test_aid.test_base import FlaskTestBase

logger = getLogger("makeradmin")


class SieFileTest(FlaskTestBase):
    models = [core.models, shop.models]

    def setUp(self) -> None:
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostCenter).delete()

    def test_verification_string(self) -> None:
        period = datetime(2023, 1, 2).strftime("%Y-%m")
        verification = Verification(period, {}, {}, "B")
        verification_str = verification_string(verification, 1)

        assert f'#VER B 1 20230101 "MakerAdmin"' == verification_str

    def test_transaction_string(self) -> None:
        account = self.db.create_transaction_account(account=f"account")
        cost_center = self.db.create_transaction_cost_center(cost_center=f"cost center")
        sum = Decimal("100.0")
        period = datetime(2023, 1, 2).strftime("%Y-%m")
        description = "test"
        transaction_str = transaction_string(account, cost_center, sum, period, description)

        assert f'#TRANS account {{1 "cost center"}} 100.0 20230101 "test"' == transaction_str

    def test_transaction_string_cc_none(self) -> None:
        account = self.db.create_transaction_account(account=f"account")
        cost_center = None
        sum = Decimal("100.0")
        period = datetime(2023, 1, 2).strftime("%Y-%m")
        description = "test"
        transaction_str = transaction_string(account, cost_center, sum, period, description)

        assert f'#TRANS account {{}} 100.0 20230101 "test"' == transaction_str


class SieFileWithVerificationTest(FlaskTestBase):
    models = [core.models, shop.models]
    number_of_verifications = 3
    number_of_transactions = 4

    def setUp(self) -> None:
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostCenter).delete()

        self.verifications: List[Verification] = []
        self.accounts: List[TransactionAccount] = []
        self.cost_centers: List[TransactionCostCenter] = []

        for i in range(1, self.number_of_verifications + 1):
            account = self.db.create_transaction_account(account=f"account{i}")
            self.accounts.append(account)
        for j in range(1, self.number_of_transactions + 1):
            cost_center = self.db.create_transaction_cost_center(cost_center=f"cost_center{j}")
            self.cost_centers.append(cost_center)

        for i in range(self.number_of_verifications):
            period = datetime(2023, i + 1, i + 3).strftime("%Y-%m")
            amounts: Dict[Tuple[TransactionAccount | None, TransactionCostCenter | None], Decimal] = {}
            types: Dict[Tuple[TransactionAccount | None, TransactionCostCenter | None], AccountingEntryType] = {}

            for j in range(self.number_of_transactions):
                iter_price = Decimal(f"{(i+1) * (j+1) + (j+1)}")
                if j % 2 == 0:
                    entry_type = AccountingEntryType.DEBIT
                    amount = Decimal("1000") + iter_price
                else:
                    entry_type = AccountingEntryType.CREDIT
                    amount = iter_price
                amounts[(self.accounts[i], self.cost_centers[j])] = amount
                types[(self.accounts[i], self.cost_centers[j])] = entry_type

            verification = Verification(period, amounts, types, "B")
            self.verifications.append(verification)

    def test_get_accounts_header(self) -> None:
        random.shuffle(self.verifications)
        acc_header = get_account_header(self.verifications)

        self.accounts.sort(key=lambda x: x.account if x else "")
        for account in self.accounts:
            pos = acc_header.index(f'#KONTO {account.account} "{account.description}"')
            acc_header.pop(pos)
        assert len(acc_header) == 0

    def test_get_cost_centers_header(self) -> None:
        random.shuffle(self.verifications)
        cc_header = get_cost_center_header(self.verifications)

        self.cost_centers.sort(key=lambda x: x.cost_center if x else "")
        for cost_center in self.cost_centers:
            pos = cc_header.index(f'#OBJEKT 1 "{cost_center.cost_center}" "{cost_center.description}"')
            cc_header.pop(pos)
        assert len(cc_header) == 0

    def test_convert_to_sie_format(self) -> None:
        sie_rows = convert_to_sie_format(self.verifications)

        for i in range(1, self.number_of_verifications + 1):
            verification_row = sie_rows.pop(0)
            assert verification_row.startswith(f'#VER B {i} 2023{i:02d}01 "MakerAdmin"')
            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "{"

            for j in range(1, self.number_of_transactions + 1):
                transaction_row = sie_rows.pop(0)
                if (j - 1) % 2 == 0:
                    assert transaction_row.startswith(
                        f'#TRANS account{i} {{1 "cost_center{j}"}} {Decimal("1000") + Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )
                else:
                    assert transaction_row.startswith(
                        f'#TRANS account{i} {{1 "cost_center{j}"}} -{Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
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

        while True:
            row = sie_rows.pop(0)

            if row.startswith("#GEN"):
                assert datetime.now().strftime("%Y%m%d") in row
                assert signer in row

            if row.startswith("#DIM"):
                assert "Kostnadställe" in row

            if row.startswith("#KONTO"):
                assert "account" in row

            if row.startswith("#OBJEKT"):
                assert "cost_center" in row

            if row.startswith("#VER"):
                break

        for i in range(1, self.number_of_verifications + 1):
            verification_row = sie_rows.pop(0) if i != 1 else row
            assert verification_row.startswith(f'#VER B {i} 2023{i:02d}01 "MakerAdmin"')
            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "{"

            for j in range(1, self.number_of_transactions + 1):
                transaction_row = sie_rows.pop(0)
                if (j - 1) % 2 == 0:
                    assert transaction_row.startswith(
                        f'#TRANS account{i} {{1 "cost_center{j}"}} {Decimal("1000") + Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )
                else:
                    assert transaction_row.startswith(
                        f'#TRANS account{i} {{1 "cost_center{j}"}} -{Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
                    )

            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "}"

        assert len(sie_rows) == 0
