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
from shop.accounting.accounting import (
    AccountingEntryType,
    TransactionAccount,
    TransactionCostcenter,
    TransactionWithAccounting,
)
from shop.accounting.verification import Verification, create_verificatons
from shop.stripe_payment_intent import CompletedPayment
from test_aid.test_base import FlaskTestBase

from api.src.basic_types.time_period import TimePeriod, date_to_period

logger = getLogger("makeradmin")


class VerificationTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostcenter).delete()

    def test_create_verificatons_simple(self) -> None:
        transactions: List[TransactionWithAccounting] = []
        num_payments = 10
        groups = [i + 1 for i in range(num_payments)]
        random.shuffle(groups)
        account = self.db.create_transaction_account(account="acc1")
        cost_center = self.db.create_transaction_cost_center(cost_center="cc1")
        period = TimePeriod.Month

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = Decimal("100") + Decimal(i)
            type = AccountingEntryType.CREDIT if i % 2 == 0 else AccountingEntryType.DEBIT
            transactions.append(TransactionWithAccounting(i, i, amount, created, account, cost_center, type))

        verifications = create_verificatons(transactions, period)

        assert len(verifications) == num_payments
        for verification, transaction in zip(verifications, transactions):
            assert verification.amounts == {(account, cost_center): transaction.amount}
            assert verification.types == {(account, cost_center): transaction.type}

    def test_create_verifications_multiple_per_period(self) -> None:
        transactions: List[TransactionWithAccounting] = []
        num_payments = 10
        num_groups = 3
        groups = [int(i / (num_payments / num_groups)) + 1 for i in range(num_payments)]
        random.shuffle(groups)
        account = self.db.create_transaction_account(account="acc1")
        cost_center = self.db.create_transaction_cost_center(cost_center="cc1")
        true_ammounts: Dict[str, Decimal] = {}
        period = TimePeriod.Month

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = Decimal("100") + Decimal(i)

            date = date_to_period(created, period)
            if date in true_ammounts:
                true_ammounts[date] += amount
            else:
                true_ammounts[date] = amount

            transactions.append(
                TransactionWithAccounting(i, i, amount, created, account, cost_center, AccountingEntryType.CREDIT)
            )

        verifications = create_verificatons(transactions, period)
        verifications_dict = {verification.period: verification for verification in verifications}

        assert len(verifications) == num_groups
        for date, amount in true_ammounts.items():
            assert verifications_dict[date].amounts == {(account, cost_center): amount}
            assert verifications_dict[date].types == {(account, cost_center): AccountingEntryType.CREDIT}

    def test_create_verifications_multiple_accounts(self) -> None:
        transactions: List[TransactionWithAccounting] = []
        true_ammounts: Dict[Tuple[str, TransactionAccount | None, TransactionCostcenter | None], Decimal] = {}

        num_payments = 100
        num_groups = 4
        num_accounts = 4
        num_cost_centers = 6
        period = TimePeriod.Month
        groups = [int(i / (num_payments / num_groups)) + 1 for i in range(num_payments)]

        true_accounts: List[TransactionAccount | None] = [None]
        true_cost_centers: List[TransactionCostcenter | None] = [None]
        for i in range(1, num_accounts):
            true_accounts.append(self.db.create_transaction_account(id=i, account="acc" + str(i + 1)))
        for i in range(1, num_cost_centers):
            true_cost_centers.append(self.db.create_transaction_cost_center(id=i, cost_center="cc" + str(i + 1)))

        accounts = [true_accounts[int(i / (num_payments / num_accounts))] for i in range(num_payments)]
        cost_centers = [true_cost_centers[int(i / (num_payments / num_cost_centers))] for i in range(num_payments)]

        iter = 0
        true_types: Dict[Tuple[TransactionAccount | None, TransactionCostcenter | None], AccountingEntryType] = {}
        for acc in accounts:
            for cc in cost_centers:
                true_types[(acc, cc)] = AccountingEntryType.CREDIT if iter % 2 == 0 else AccountingEntryType.DEBIT
                iter += 1

        random.shuffle(groups)
        random.shuffle(accounts)
        random.shuffle(cost_centers)

        # If we get the comibination of None, None for the accounting we have to change because it is invalid to have two Nones
        for i in range(num_payments):
            if accounts[i] is None and cost_centers[i] is None:
                accounts[i] = true_accounts[0]

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = Decimal("100") + Decimal(i)

            date = date_to_period(created, period)
            key = (date, accounts[i], cost_centers[i])
            if key in true_ammounts:
                true_ammounts[key] += amount
            else:
                true_ammounts[key] = amount

            transactions.append(
                TransactionWithAccounting(
                    i, i, amount, created, accounts[i], cost_centers[i], true_types[(accounts[i], cost_centers[i])]
                )
            )

        verifications = create_verificatons(transactions, period)
        verifications_dict = {verification.period: verification for verification in verifications}

        assert len(verifications) == num_groups
        for period, verification in verifications_dict.items():
            for accounting_key in verification.amounts:
                true_amount_key = (period, accounting_key[0], accounting_key[1])
                assert verifications_dict[period].amounts[accounting_key] == true_ammounts[true_amount_key]
                assert verification.types[accounting_key] == true_types[accounting_key]
