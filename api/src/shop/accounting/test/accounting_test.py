import random
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple
from unittest import TestCase
from unittest.mock import Mock, patch

import core
import membership
import pytz
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


class AccountingDifferenceTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostcenter).delete()
        db_session.query(ProductAccountsCostCenters).delete()

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
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

        self.number_of_products = 1
        self.number_of_accounts = 2
        self.number_of_cost_centers = 1

        for i in range(self.number_of_accounts):
            self.db.create_transaction_account()
        self.transaction_accounts = db_session.query(TransactionAccount).all()
        random.shuffle(self.transaction_accounts)

        for i in range(self.number_of_cost_centers):
            self.db.create_transaction_cost_center()
        self.transaction_cost_centers = db_session.query(TransactionCostcenter).all()
        random.shuffle(self.transaction_cost_centers)

        product_category = self.db.create_category()
        for i in range(self.number_of_products):
            product = self.db.create_product(category_id=product_category.id)
            fractions_left = {type: 100 for type in AccountingEntryType}
            for j in range(self.number_of_accounts):
                for k in range(self.number_of_cost_centers):
                    for type in AccountingEntryType:
                        fraction = random.randint(1, round(fractions_left[type] / 1.5))
                        logger.info(f"type: {type}")
                        logger.info(f"fraction: {fraction}")
                        fractions_left[type] -= fraction
                        if j > k:
                            self.db.create_product_account_cost_center(
                                product_id=product.id,
                                account_id=self.transaction_accounts[j].id,
                                cost_center_id=self.transaction_cost_centers[k].id,
                                type=type.value,
                                fraction=fraction,
                            )
                        elif j == k:
                            self.db.create_product_account_cost_center(
                                product_id=product.id,
                                account_id=self.transaction_accounts[j].id,
                                cost_center_id=None,
                                type=type.value,
                                fraction=fraction,
                            )
            for type in AccountingEntryType:
                fraction = fractions_left[type]
                logger.info(f"type: {type}")
                logger.info(f"fraction: {fraction}")
                self.db.create_product_account_cost_center(
                    product_id=product.id,
                    account_id=None,
                    cost_center_id=self.transaction_cost_centers[0].id,
                    type=type.value,
                    fraction=fraction,
                )

    def test_product_to_accounting(self) -> None:
        def custom_sort_key(item: Any) -> Tuple[str, str]:
            account_value = str(item.account.account) if item.account else "0"
            cost_center_value = str(item.cost_center.cost_center) if item.cost_center else "0"
            return (account_value, cost_center_value)

        prod_to_account = ProductToAccountCostCenter()

        for product in db_session.query(Product).all():
            db_info = (
                db_session.query(ProductAccountsCostCenters)
                .outerjoin(TransactionAccount, ProductAccountsCostCenters.account)
                .outerjoin(TransactionCostcenter, ProductAccountsCostCenters.cost_center)
                .filter(ProductAccountsCostCenters.product_id == product.id)
                .all()
            )
            accounting = prod_to_account.get_account_cost_center(product.id)
            assert len(accounting) == len(db_info)
            accounting.sort(key=lambda x: ((x.account or "0"), (x.cost_center or "0")))
            db_info.sort(key=custom_sort_key)

            for acc, product_info in zip(accounting, db_info):
                assert acc.fraction > 1
                assert acc.fraction <= 100
                assert acc.fraction == product_info.fraction
                assert acc.type == AccountingEntryType(product_info.type)

                if product_info.account is None:
                    assert acc.account is None
                else:
                    assert acc.account == product_info.account.account
                if product_info.cost_center is None:
                    assert acc.cost_center is None
                else:
                    assert acc.cost_center == product_info.cost_center.cost_center

    # TODO test failing fractions and double nones ok check


class SplitTransactionsTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    def test_split_transactions_over_accounts_simple(self, mock_product_to_accounting: Mock) -> None:
        def get_accounting_side_effect(*args, **kwargs) -> List[AccountCostCenter]:
            return [AccountCostCenter("acc" + str(args[0]), "cc" + str(args[0]), args[0], AccountingEntryType.CREDIT)]

        num_transactions = 5
        num_products = 2
        amounts = [100 + 10 * i for i in range(num_transactions)]

        member = self.db.create_member()
        product_category = self.db.create_category()
        true_info: Dict[datetime, Dict[Decimal, int]] = {}
        for i in range(num_transactions):
            created = datetime(2023, 3, i + 1, tzinfo=timezone.utc)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=amounts[i], created_at=created)

            product_info: Dict[Decimal, int] = {}
            for j in range(num_products):
                product_price = amounts[i] / num_products
                product = self.db.create_product(category_id=product_category.id, price=product_price)
                product_info[product_price * product.id] = product.id
                self.db.create_transaction_content(
                    transaction_id=transaction.id, product_id=product.id, amount=product_price, count=1
                )
            true_info[created] = product_info

        transactions = db_session.query(Transaction).join(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = get_accounting_side_effect

        accounting = split_transactions_over_accounts(transactions)

        assert len(accounting) == num_transactions * num_products
        for acc in accounting:
            timezone_aware_date = acc.date.replace(tzinfo=pytz.UTC)
            product_id = true_info[timezone_aware_date][acc.amount]
            assert acc.account == "acc" + str(product_id)
            assert acc.cost_center == "cc" + str(product_id)
            assert acc.type == AccountingEntryType.CREDIT

    # TODO some split test with more variation and different types
    # different number of product counts in transaction content
    # with some none cost center and account in the test

    # TODO a test with odd fractions to test rounding

    # TODO a test without the mock, inherit ProductToAccountCostCenterTest
