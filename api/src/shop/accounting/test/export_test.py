from logging import getLogger
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest import TestCase

from shop.stripe_payment_intent import CompletedPayment
from shop.accounting.accounting import AmountPerAccountAndCostCenter
from shop.accounting.export import export_accounting, transaction_fees_to_transaction_with_accounting
from shop.accounting.verification import Verification

logger = getLogger("makeradmin")


class ExportTest(TestCase):
    def test_fees_to_transaction_with_accounting(self) -> None:
        completed_payments: List[CompletedPayment] = []
        num_payments = 10
        num_groups = 3
        groups = [int(i / num_groups) + 1 for i in range(num_payments)]
        true_fees: Dict[str, Decimal] = {}
        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            fee = 10 + i
            date = created.strftime("%Y-%m")
            if date in true_fees:
                true_fees[date] += fee
            else:
                true_fees[date] = fee
            payment = CompletedPayment(i, 100 * i, created, fee)
            completed_payments.append(payment)

        transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)

        for period, fee in transaction_fees.items():
            self.assertEqual(fee, true_fees[period])

    def test_export_accounting(self) -> None:
        pass
