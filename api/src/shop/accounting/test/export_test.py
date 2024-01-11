from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase
from unittest.mock import Mock, patch

import core
import membership
import pytest
import shop
from basic_types.time_period import TimePeriod, date_to_period
from membership.models import Member
from service.db import db_session
from shop.accounting.accounting import TransactionWithAccounting
from shop.accounting.export import export_accounting, transaction_fees_to_transaction_with_accounting
from shop.accounting.test.accounting_test import SplitTransactionsWithoutMockTest
from shop.accounting.verification import Verification
from shop.models import (
    Product,
    ProductAccountsCostCenters,
    ProductCategory,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostcenter,
)
from shop.stripe_payment_intent import CompletedPayment
from test_aid.test_base import FlaskTestBase

logger = getLogger("makeradmin")


class ExportTest(TestCase):
    def test_fees_to_transaction_with_accounting(self) -> None:
        completed_payments: Dict[int, CompletedPayment] = {}
        num_payments = 10
        num_groups = 3
        groups = [int(i / num_groups) + 1 for i in range(num_payments)]
        true_fees: List[Decimal] = []
        for i in range(num_payments):
            group = groups[i]
            created = datetime(2023, group, 1, tzinfo=timezone.utc)
            fee = Decimal("10.0") + Decimal(i)
            true_fees.append(fee)
            payment = CompletedPayment(i, Decimal("100.0") * Decimal(i), created, fee)
            completed_payments[i] = payment

        transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)

        for i in range(num_payments):
            self.assertEqual(transaction_fees[i].amount, true_fees[i])
            assert transaction_fees[i].account == "6573"
            assert transaction_fees[i].cost_center == "Föreningsgemensamt"


class AccountingExportWithStripeMockTest(SplitTransactionsWithoutMockTest):
    def setUp(self) -> None:
        super().setUp()

    @patch("shop.accounting.export.get_completed_payments_from_stripe")
    def test_export_accounting(self, get_payments_from_stripe: Mock) -> None:
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        get_payments_from_stripe.return_value = self.completed_payments
        sie_str = export_accounting(start_date, end_date, TimePeriod.Month, self.member)
