import random
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase

from basic_types.enums import AccountingEntryType
from shop.accounting.accounting import TransactionWithAccounting
from shop.accounting.verification import Verification, create_verificatons
from shop.stripe_payment_intent import CompletedPayment

logger = getLogger("makeradmin")


class VerificationTest(TestCase):
    def test_create_verificatons_simple(self) -> None:
        transactions: List[TransactionWithAccounting] = []
        num_payments = 10
        groups = [i + 1 for i in range(num_payments)]
        random.shuffle(groups)

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = 100 + i
            type = AccountingEntryType.CREDIT if i % 2 == 0 else AccountingEntryType.DEBIT
            transactions.append(TransactionWithAccounting(i, i, amount, created, "1", "1", type))

        verifications = create_verificatons(transactions)

        assert len(verifications) == num_payments
        for verification, transaction in zip(verifications, transactions):
            assert verification.amounts == {("1", "1"): transaction.amount}
            assert verification.types == {("1", "1"): transaction.type}

    def test_create_verifications_multiple_per_period(self) -> None:
        transactions: List[TransactionWithAccounting] = []
        num_payments = 10
        num_groups = 3
        groups = [int(i / (num_payments / num_groups)) + 1 for i in range(num_payments)]
        random.shuffle(groups)
        true_ammounts: Dict[str, Decimal] = {}

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = 100 + i

            date = created.strftime("%Y-%m")
            if date in true_ammounts:
                true_ammounts[date] += amount
            else:
                true_ammounts[date] = amount

            transactions.append(TransactionWithAccounting(i, i, amount, created, "1", "1", AccountingEntryType.CREDIT))

        verifications = create_verificatons(transactions)
        verifications_dict = {verification.period: verification for verification in verifications}

        assert len(verifications) == num_groups
        for date, amount in true_ammounts.items():
            assert verifications_dict[date].amounts == {("1", "1"): amount}
            assert verifications_dict[date].types == {("1", "1"): AccountingEntryType.CREDIT}

    def test_create_verifications_multiple_accounts(self) -> None:
        transactions: List[TransactionWithAccounting] = []
        true_ammounts: Dict[Tuple[str, str, str], Decimal] = {}

        num_payments = 100
        num_groups = 4
        num_accounts = 4
        num_cost_centers = 6
        groups = [int(i / (num_payments / num_groups)) + 1 for i in range(num_payments)]
        accounts = [str(int(i / (num_payments / num_accounts))) for i in range(num_payments)]
        accounts = [None if account == "0" else account for account in accounts]
        cost_centers = [str(int(i / (num_payments / num_cost_centers))) for i in range(num_payments)]
        cost_centers = [None if cost_center == "0" else cost_center for cost_center in cost_centers]

        iter = 0
        true_types: Dict[Tuple[str | None, str | None], AccountingEntryType] = {}
        for acc in accounts:
            for cc in cost_centers:
                true_types[(acc, cc)] = AccountingEntryType.CREDIT if iter % 2 == 0 else AccountingEntryType.DEBIT
                iter += 1

        random.shuffle(groups)
        random.shuffle(accounts)
        random.shuffle(cost_centers)

        for i in range(num_payments):
            if accounts[i] is None and cost_centers[i] is None:
                accounts[i] = "1"

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = 100 + i

            date = created.strftime("%Y-%m")
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

        verifications = create_verificatons(transactions)
        verifications_dict = {verification.period: verification for verification in verifications}

        assert len(verifications) == num_groups
        for period, verification in verifications_dict.items():
            for accounting_key in verification.amounts:
                true_amount_key = (period, accounting_key[0], accounting_key[1])
                assert verifications_dict[period].amounts[accounting_key] == true_ammounts[true_amount_key]
                assert verification.types[accounting_key] == true_types[accounting_key]
