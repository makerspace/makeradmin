from logging import getLogger
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest import TestCase

from shop.stripe_payment_intent import CompletedPayment
from shop.accounting.accounting import AmountPerAccountAndCostCenter
from shop.accounting.verification import Verification, create_verificatons, group_amounts, group_transaction_fees

logger = getLogger("makeradmin")


class AccountingTest(TestCase):
    def test_group_transaction_fees(self) -> None:
        pass
