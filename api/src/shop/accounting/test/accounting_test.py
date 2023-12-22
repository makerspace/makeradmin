from logging import getLogger
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch, Mock

import core
import membership
import shop
from service.db import db_session
from shop.stripe_payment_intent import CompletedPayment
from membership.models import Member
from shop.models import Transaction, TransactionContent, Product
from shop.accounting.accounting import (
    AmountPerAccountAndCostCenter,
    AccountCostCenter,
    ProductToAccountCostCenter,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.verification import Verification
from test_aid.test_base import FlaskTestBase

logger = getLogger("makeradmin")


class AccountingTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

    def test_product_to_accounting(self) -> None:
        pass

    def test_diff_transactions_payments(self) -> None:
        pass

    # TODO include some none cost center in the test
    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    def test_split_transactions_over_accounts(self, mock_product_to_accounting: Mock) -> None:
        def get_accounting_side_effect(*args, **kwargs) -> List[AccountCostCenter]:
            return [AccountCostCenter(str(args[0]), str[args[0]], args[0] / 10, args[0] / 100)]  # TODO fix

        num_transactions = 5
        num_products = [int(i / num_transactions) + 1 for i in range(num_transactions)]
        amounts = [100 + 10 * i for i in range(num_transactions)]

        member = self.db.create_member()
        product_category = self.db.create_category()
        product = self.db.create_product(category_id=product_category.id)
        for i in range(num_transactions):
            transaction = self.db.create_transaction(member_id=member.member_id, amount=amounts[i])

            for j in range(num_products[i]):
                self.db.create_transaction_content(
                    transaction_id=transaction.id, product_id=product.id, amount=amounts[i] / num_products[i]
                )

        transactions = db_session.query(Transaction).all()
        assert transactions
        assert len(transactions) == num_transactions

        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = get_accounting_side_effect

        split_transactions_over_accounts(transactions)

        assert False

    # TODO a test without the mock

    # TODO a test with odd fractions to test rounding
