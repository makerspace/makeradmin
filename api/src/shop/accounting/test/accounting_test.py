from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase
from unittest.mock import Mock, patch

import core
import membership
import shop
from basic_types.enums import AccountingEntryType
from membership.models import Member
from service.db import db_session
from shop.accounting.accounting import (
    AccountCostCenter,
    ProductToAccountCostCenter,
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.verification import Verification
from shop.models import Product, Transaction, TransactionContent
from shop.stripe_payment_intent import CompletedPayment
from test_aid.test_base import FlaskTestBase

logger = getLogger("makeradmin")


class AccountingTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

    def test_diff_transactions_and_completed_payments(self) -> None:
        pass

    def test_product_to_accounting(self) -> None:
        pass

    # TODO test failing table ok check

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    def test_split_transactions_over_accounts(self, mock_product_to_accounting: Mock) -> None:
        def get_accounting_side_effect(*args, **kwargs) -> List[AccountCostCenter]:
            logger.info("args")
            logger.info(args[0])
            return [AccountCostCenter(str(args[0]), str(args[0]), args[0] / 10, AccountingEntryType.CREDIT)]

        num_transactions = 5
        num_products = 2
        amounts = [100 + 10 * i for i in range(num_transactions)]

        member = self.db.create_member()
        product_category = self.db.create_category()
        product = self.db.create_product(category_id=product_category.id)
        for i in range(num_transactions):
            transaction = self.db.create_transaction(member_id=member.member_id, amount=amounts[i])

            for j in range(num_products):
                self.db.create_transaction_content(
                    transaction_id=transaction.id, product_id=product.id, amount=amounts[i] / num_products
                )

        transactions = db_session.query(Transaction).all()
        assert transactions
        assert len(transactions) == num_transactions

        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = get_accounting_side_effect

        accounting = split_transactions_over_accounts(transactions)

        assert len(accounting) == num_transactions * num_products
        # TODO more asserts

    # TODO test split with some none cost center and account in the test

    # TODO some split test with more variation and different types

    # TODO a test without the mock

    # TODO a test with odd fractions to test rounding
