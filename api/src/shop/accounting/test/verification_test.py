from logging import getLogger
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest import TestCase

from shop.stripe_payment_intent import CompletedPayment
from shop.accounting.accounting import AmountPerAccountAndCostCenter
from shop.accounting.verification import Verification, create_verificatons, group_amounts, group_transaction_fees

logger = getLogger("makeradmin")


class VerificationTest(TestCase):
    def test_group_transaction_fees(self) -> None:
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

        transaction_fees = group_transaction_fees(completed_payments)

        for period, fee in transaction_fees.items():
            self.assertEqual(fee, true_fees[period])

    def test_group_amounts(self) -> None:
        amounts: List[AmountPerAccountAndCostCenter] = []
        num_payments = 10
        num_groups = 3
        groups = [int(i / num_groups) + 1 for i in range(num_payments)]

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            amount = 100 + i
            amounts.append(AmountPerAccountAndCostCenter(amount, created, 1, "1"))

        grouped_amounts = group_amounts(amounts)

        for amount in amounts:
            self.assertIn(amount, grouped_amounts[amount.date.strftime("%Y-%m")])

    def test_crate_verifications(self) -> None:
        completed_payments: List[CompletedPayment] = []
        amounts: List[AmountPerAccountAndCostCenter] = []
        num_payments = 10
        num_groups = 3
        groups = [int(i / num_groups) + 1 for i in range(num_payments)]
        true_fees: Dict[str, Decimal] = {}
        true_ammounts: Dict[str, Decimal] = {}

        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            fee = 10 + i
            amount = 100 + i

            date = created.strftime("%Y-%m")
            if date in true_fees:
                true_fees[date] += fee
            else:
                true_fees[date] = fee
            if date in true_ammounts:
                true_ammounts[date] += amount
            else:
                true_ammounts[date] = amount

            payment = CompletedPayment(i, amount, created, fee)
            completed_payments.append(payment)
            amounts.append(AmountPerAccountAndCostCenter(amount, created, 1, "1"))

        verifications = create_verificatons(amounts, completed_payments)
        verifications_dict = {verification.period: verification for verification in verifications}

        for amount in amounts:
            self.assertIn(amount, verifications_dict[amount.date.strftime("%Y-%m")].amounts)

        for verification in verifications:
            self.assertEqual(verification.total_transaction_fee, true_fees[verification.period])
            self.assertEqual(
                verification.total_amount_ex_fee,
                true_ammounts[verification.period] - true_fees[verification.period],
            )
