import random
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase

import core
import membership
import pytest
import shop
from service.db import db_session
from shop.accounting.accounting import AccountingEntryType, TransactionAccount, TransactionCostcenter
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
        db_session.query(TransactionCostcenter).delete()

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
        account = self.db.create_transaction_account(account=f"account")
        cost_center = self.db.create_transaction_cost_center(cost_center=f"cost center")
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
        account = self.db.create_transaction_account(account=f"account")
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


class SieFileWithVerificationTest(FlaskTestBase):
    models = [core.models, shop.models]
    number_of_verifications = 2
    number_of_transactions = 3

    def setUp(self) -> None:
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostcenter).delete()

        self.verifications: List[Verification] = []
        self.accounts: List[TransactionAccount] = []
        self.cost_centers: List[TransactionCostcenter] = []

        for i in range(1, self.number_of_verifications + 1):
            period = datetime(
                2023,
                i,
                i + 3,
            ).strftime("%Y-%m")
            amounts: Dict[Tuple[TransactionAccount | None, TransactionCostcenter | None], Decimal] = {}
            types: Dict[Tuple[TransactionAccount | None, TransactionCostcenter | None], AccountingEntryType] = {}

            for j in range(1, self.number_of_transactions + 1):
                account = self.db.create_transaction_account(account=f"account{j}")
                cost_center = self.db.create_transaction_cost_center(cost_center=f"cost_center{j}")
                self.accounts.append(account)
                self.cost_centers.append(cost_center)

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

    def test_get_accounts_header(self) -> None:
        random.shuffle(self.verifications)
        acc_header = get_account_header(self.verifications)

        self.accounts.sort(key=lambda x: x.account if x else "")
        for account in self.accounts:
            assert f'#KONTO {account.account} "{account.description}"' in acc_header

    def test_get_cost_centers_header(self) -> None:
        random.shuffle(self.verifications)
        cc_header = get_cost_center_header(self.verifications)

        self.cost_centers.sort(key=lambda x: x.cost_center if x else "")
        for cost_center in self.cost_centers:
            assert f'#OBJEKT 1 "{cost_center.cost_center}" "{cost_center.description}"' in cc_header

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

        logger.info(sie_str)

        sie_rows = sie_str.split("\n")

        while True:
            row = sie_rows.pop(0)

            if row.startswith("#GEN"):
                assert datetime.now().strftime("%Y%m%d") in row
                assert signer in row

            if row.startswith("#DIM"):
                assert "Kostnadställe" in row

            if row.startswith("#VER"):
                break

        for i in range(1, self.number_of_verifications + 1):
            verification_row = sie_rows.pop(0) if i != 1 else row
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
