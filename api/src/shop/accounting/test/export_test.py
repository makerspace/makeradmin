from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase

from shop.accounting.accounting import TransactionWithAccounting
from shop.accounting.export import export_accounting, transaction_fees_to_transaction_with_accounting
from shop.accounting.verification import Verification
from shop.stripe_payment_intent import CompletedPayment

logger = getLogger("makeradmin")


class ExportTest(TestCase):
    def test_fees_to_transaction_with_accounting(self) -> None:
        completed_payments: List[CompletedPayment] = []
        num_payments = 10
        num_groups = 3
        groups = [int(i / num_groups) + 1 for i in range(num_payments)]
        true_fees: List[Decimal] = []
        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            fee = 10 + i
            true_fees.append(fee)
            payment = CompletedPayment(i, 100 * i, created, fee)
            completed_payments.append(payment)

        transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)

        for i in range(num_payments):
            self.assertEqual(transaction_fees[i].amount, true_fees[i])
            assert transaction_fees[i].account == "6573"
            assert transaction_fees[i].cost_center == "Föreningsgemensamt"

    # TODO mock things
    def test_export_accounting(self) -> None:
        pass

    # TODO some larger export test
