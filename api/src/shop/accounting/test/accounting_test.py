import random
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
from shop.models import Product, Transaction, TransactionContent
from shop.stripe_payment_intent import CompletedPayment
from test_aid.test_base import FlaskTestBase

logger = getLogger("makeradmin")


class AccountingDifferenceTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

        self.num_transactions = 10
        self.amounts = [100 + 10 * i for i in range(self.num_transactions)]

        self.completed_payments: Dict[int, CompletedPayment] = {}

        self.member = self.db.create_member()
        for i in range(self.num_transactions):
            transaction = self.db.create_transaction(member_id=self.member.member_id, amount=self.amounts[i])

        self.transactions = db_session.query(Transaction).all()

        created = datetime(2023, 6, 1, tzinfo=timezone.utc)
        for i, transaction in enumerate(self.transactions):
            payment = CompletedPayment(transaction.id, self.amounts[i], created, 10)
            self.completed_payments[transaction.id] = payment

        # Add some failed transactions that should be ignored by the diff
        self.db.create_transaction(member_id=self.member.member_id, amount=50, status=Transaction.PENDING)
        self.db.create_transaction(member_id=self.member.member_id, amount=20, status=Transaction.FAILED)
        self.transactions = db_session.query(Transaction).all()

    def test_diff_transactions_and_completed_payments_no_dif(self) -> None:
        random.shuffle(self.transactions)
        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
        assert len(diff) == 0

    def test_diff_transactions_and_completed_payments_extra_stripe(self) -> None:
        created = datetime(2023, 6, 1, tzinfo=timezone.utc)
        id = 404
        extra_payment = CompletedPayment(id, 500, created, 10)
        self.completed_payments[id] = extra_payment

        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
        logger.info(diff)
        assert len(diff) == 1
        transaction = diff[0][0]
        payment = diff[0][1]
        assert transaction is None
        assert payment.amount == extra_payment.amount
        assert payment.transaction_id == extra_payment.transaction_id

    def test_diff_transactions_and_completed_payments_extra_makeradmin(self) -> None:
        extra_transaction = self.db.create_transaction(
            member_id=self.member.member_id, amount=50, status=Transaction.COMPLETED
        )
        self.transactions.append(extra_transaction)
        random.shuffle(self.transactions)

        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
        assert len(diff) == 1
        transaction = diff[0][0]
        payment = diff[0][1]
        assert payment is None
        assert transaction.amount == extra_transaction.amount
        assert transaction.id == extra_transaction.id

    def test_diff_transactions_and_completed_payments_wrong_stripe_amount(self) -> None:
        created = datetime(2023, 6, 1, tzinfo=timezone.utc)
        correct_transaction = self.transactions[0]
        self.completed_payments[correct_transaction.id] = CompletedPayment(
            correct_transaction.id, correct_transaction.amount + 1, created, 10
        )
        wrong_payment = self.completed_payments[correct_transaction.id]

        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
        assert len(diff) == 1
        transaction = diff[0][0]
        payment = diff[0][1]
        assert payment.amount == wrong_payment.amount
        assert payment.amount != correct_transaction.amount
        assert transaction.amount == correct_transaction.amount
        assert payment.transaction_id == wrong_payment.transaction_id
        assert payment.transaction_id == correct_transaction.id
        assert transaction.id == correct_transaction.id
        assert transaction.id == wrong_payment.transaction_id

    def test_diff_transactions_and_completed_payments_wrong_makeradmin_amount(self) -> None:
        self.transactions[0].amount += 10
        wrong_transaction = self.transactions[0]
        correct_payment = self.completed_payments[wrong_transaction.id]
        random.shuffle(self.transactions)

        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
        assert len(diff) == 1
        transaction = diff[0][0]
        payment = diff[0][1]
        assert payment.amount == correct_payment.amount
        assert payment.amount != wrong_transaction.amount
        assert transaction.amount == wrong_transaction.amount
        assert payment.transaction_id == correct_payment.transaction_id
        assert payment.transaction_id == wrong_transaction.id
        assert transaction.id == wrong_transaction.id


class ProductToAccountCostCenterTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

    def test_product_to_accounting(self) -> None:
        pass

    # TODO test failing fractions and double nones ok check


class AccountingTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

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
