import random
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple
from unittest import TestCase
from unittest.mock import Mock, patch

import core
import membership
import pytest
import shop
from basic_types.enums import AccountingEntryType
from membership.models import Member
from service.db import db_session
from service.error import InternalServerError
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
        self.amounts = [Decimal("100.0") + Decimal("11.3") * Decimal(i) for i in range(self.num_transactions)]

        self.completed_payments: Dict[int, CompletedPayment] = {}

        self.member = self.db.create_member()
        for i in range(self.num_transactions):
            transaction = self.db.create_transaction(member_id=self.member.member_id, amount=self.amounts[i])

        self.transactions = db_session.query(Transaction).all()

        created = datetime(2023, 6, 1, tzinfo=timezone.utc)
        for i, transaction in enumerate(self.transactions):
            payment = CompletedPayment(transaction.id, self.amounts[i], created, Decimal("10"))
            self.completed_payments[transaction.id] = payment

        # Add some failed transactions that should be ignored by the diff
        self.db.create_transaction(member_id=self.member.member_id, amount=Decimal("50"), status=Transaction.PENDING)
        self.db.create_transaction(member_id=self.member.member_id, amount=Decimal("20"), status=Transaction.FAILED)
        self.transactions = db_session.query(Transaction).all()

    def test_diff_transactions_and_completed_payments_no_diff(self) -> None:
        random.shuffle(self.transactions)
        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
        assert len(diff) == 0

    def test_diff_transactions_and_completed_payments_extra_stripe(self) -> None:
        created = datetime(2023, 6, 1, tzinfo=timezone.utc)
        id = 404
        extra_payment = CompletedPayment(id, Decimal("500"), created, Decimal("10"))
        self.completed_payments[id] = extra_payment

        diff = diff_transactions_and_completed_payments(self.transactions, self.completed_payments)
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
            correct_transaction.id, correct_transaction.amount + 1, created, Decimal("10")
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
    number_of_products = 3
    number_of_accounts = 4
    number_of_cost_centers = 3
    amounts = [Decimal("100.0") + Decimal("11.3") * Decimal(i) for i in range(number_of_products)]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

        random_scale = self.number_of_accounts * self.number_of_cost_centers / 2

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
            product_price = self.amounts[i]
            product = self.db.create_product(category_id=product_category.id, price=product_price)
            fractions_left = {type: 100 for type in AccountingEntryType}
            for j in range(self.number_of_accounts):
                for k in range(self.number_of_cost_centers):
                    for type in AccountingEntryType:
                        if j >= k:
                            max_fraction = min(fractions_left[type] / 2, 100 / random_scale)
                            fraction = random.randint(1, round(max_fraction))
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
                assert acc.fraction >= 1
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

    def test_product_to_accounting_outside_range_0(self) -> None:
        products = db_session.query(Product).all()
        self.db.create_product_account_cost_center(
            product_id=products[0].id,
            account_id=self.transaction_accounts[0].id,
            cost_center_id=self.transaction_cost_centers[0].id,
            type=AccountingEntryType.CREDIT.value,
            fraction=0,
        )
        with self.assertRaises(InternalServerError) as context:
            ProductToAccountCostCenter()
        self.assertTrue("not in range [1, 100]" in str(context.exception))

    def test_product_to_accounting_outside_range_101(self) -> None:
        products = db_session.query(Product).all()
        self.db.create_product_account_cost_center(
            product_id=products[0].id,
            account_id=self.transaction_accounts[0].id,
            cost_center_id=self.transaction_cost_centers[0].id,
            type=AccountingEntryType.CREDIT.value,
            fraction=101,
        )
        with self.assertRaises(InternalServerError) as context:
            ProductToAccountCostCenter()
        self.assertTrue("not in range [1, 100]" in str(context.exception))

    def test_product_to_accounting_fraction_not_sum_correctly_extra_entry(self) -> None:
        products = db_session.query(Product).all()
        self.db.create_product_account_cost_center(
            product_id=products[0].id,
            account_id=self.transaction_accounts[0].id,
            cost_center_id=self.transaction_cost_centers[0].id,
            type=AccountingEntryType.CREDIT.value,
            fraction=1,
        )
        with self.assertRaises(InternalServerError) as context:
            ProductToAccountCostCenter()
        self.assertTrue("fraction weights not adding up to 100" in str(context.exception))

    def test_product_to_accounting_fraction_not_sum_correctly_modified_add(self) -> None:
        accounting = db_session.query(ProductAccountsCostCenters).all()
        for acc in accounting:
            if acc.fraction < 100:
                acc.fraction = acc.fraction + 1
                break
        db_session.commit()
        with self.assertRaises(InternalServerError) as context:
            ProductToAccountCostCenter()
        self.assertTrue("fraction weights not adding up to 100" in str(context.exception))

    def test_product_to_accounting_fraction_not_sum_correctly_modified_sub(self) -> None:
        accounting = db_session.query(ProductAccountsCostCenters).all()
        for acc in accounting:
            if acc.fraction > 1:
                acc.fraction = acc.fraction - 1
                break
        db_session.commit()
        with self.assertRaises(InternalServerError) as context:
            ProductToAccountCostCenter()
        self.assertTrue("fraction weights not adding up to 100" in str(context.exception))

    def test_product_to_accounting_both_account_cost_center_are_none(self) -> None:
        products = db_session.query(Product).all()
        self.db.create_product_account_cost_center(
            product_id=products[0].id,
            account_id=None,
            cost_center_id=None,
            type=AccountingEntryType.CREDIT.value,
            fraction=100,
        )
        with self.assertRaises(InternalServerError) as context:
            ProductToAccountCostCenter()
        self.assertTrue("both account and cost center as None" in str(context.exception))


class SplitTransactionsTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()

    @staticmethod
    def assertAccounting(
        num_products: List[int],
        true_transactions: Dict[int, Transaction],
        completed_payments: Dict[int, CompletedPayment],
        accounting: List[TransactionWithAccounting],
        true_transaction_contents: Dict[int, Dict[int, TransactionContent]],
        fraction: int,
    ) -> None:
        num_entry_types_found: Dict[AccountingEntryType, int] = {type: 0 for type in AccountingEntryType}

        for acc in accounting:
            product_id = acc.product_id
            transaction = true_transactions[acc.transaction_id]
            num_entry_types_found[acc.type] += 1

            transaction_fee = completed_payments[transaction.id].fee
            amount = Decimal(true_transaction_contents[transaction.id][product_id].amount)
            amount = amount if acc.type == AccountingEntryType.CREDIT else amount - transaction_fee
            actual_amount = amount * Decimal(fraction) * Decimal("0.01")  # Multiply by 0.01 instead of dividing by 100
            assert acc.amount == pytest.approx(actual_amount, abs=0.0001)
            assert transaction.created_at == acc.date
            if product_id == 1:
                assert acc.account is None
            else:
                assert acc.type.value + "_acc" + str(product_id) in acc.account
            if product_id == 2:
                assert acc.cost_center is None
            else:
                assert acc.type.value + "_cc" + str(product_id) in acc.cost_center

        for type, count in num_entry_types_found.items():
            if fraction == 100:
                assert count == sum(num_products)
            else:
                assert count == sum(num_products) * 2

    def create_fake_data(
        self, num_transactions: int, num_products: List[int], amounts: List[Decimal]
    ) -> Tuple[Dict[int, Transaction], Dict[int, Dict[int, TransactionContent]]]:
        member = self.db.create_member()
        product_category = self.db.create_category()
        true_transaction_contents: Dict[int, Dict[int, TransactionContent]] = {}
        true_transactions: Dict[int, Transaction] = {}
        for i in range(num_transactions):
            created = datetime(2023, 3, i + 1, tzinfo=timezone.utc)
            transaction = self.db.create_transaction(member_id=member.member_id, amount=amounts[i], created_at=created)
            true_transactions[transaction.id] = transaction

            transaction_contents: Dict[int, TransactionContent] = {}
            price_left = amounts[i]
            for j in range(num_products[i]):
                if j == num_products[i] - 1:
                    product_price = price_left
                else:
                    product_price = Decimal(random.randint(1, round(amounts[i] / num_products[i]) - 1))
                    price_left -= product_price
                product = self.db.create_product(
                    id=(i * num_transactions) + j + 1, category_id=product_category.id, price=product_price
                )
                count = 1
                transaction_contents[product.id] = self.db.create_transaction_content(
                    transaction_id=transaction.id, product_id=product.id, amount=product_price * count, count=count
                )
            true_transaction_contents[transaction.id] = transaction_contents
        return true_transactions, true_transaction_contents

    @staticmethod
    def get_accounting_side_effect_one_acc_cc(product_id: int) -> List[AccountCostCenter]:
        account_cost_center: List[AccountCostCenter] = []
        for i in range(2):
            entry_type = AccountingEntryType.CREDIT if i % 2 == 0 else AccountingEntryType.DEBIT
            account = entry_type.value + "_acc" + str(product_id) + str(i)
            cost_center = entry_type.value + "_cc" + str(product_id) + str(i)
            if product_id == 1:
                account = None
            elif product_id == 2:
                cost_center = None

            account_cost_center.append(AccountCostCenter(account, cost_center, 100, entry_type))
        return account_cost_center

    @staticmethod
    def get_accounting_side_effect(product_id: int) -> List[AccountCostCenter]:
        account_cost_center: List[AccountCostCenter] = []
        for i in range(4):
            entry_type = AccountingEntryType.CREDIT if i % 2 == 0 else AccountingEntryType.DEBIT
            account = entry_type.value + "_acc" + str(product_id) + str(i)
            cost_center = entry_type.value + "_cc" + str(product_id) + str(i)
            if product_id == 1:
                account = None
            elif product_id == 2:
                cost_center = None

            account_cost_center.append(AccountCostCenter(account, cost_center, 50, entry_type))
        return account_cost_center

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    def test_split_transactions_over_accounts_simple(self, mock_product_to_accounting: Mock) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id, transaction.amount, transaction.created_at, Decimal("1.00")
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect_one_acc_cc

        accounting, leftover_amounts = split_transactions_over_accounts(transactions, completed_payments)
        assert len(leftover_amounts) == 0

        assert len(accounting) == sum(num_products) * 2
        self.assertAccounting(
            num_products, true_transactions, completed_payments, accounting, true_transaction_contents, 100
        )

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    def test_split_transactions_over_accounts_simple_odd_fee(self, mock_product_to_accounting: Mock) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id, transaction.amount, transaction.created_at, Decimal("1.23")
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect_one_acc_cc

        accounting, leftover_amounts = split_transactions_over_accounts(transactions, completed_payments)
        assert len(leftover_amounts) == 0

        assert len(accounting) == sum(num_products) * 2
        self.assertAccounting(
            num_products, true_transactions, completed_payments, accounting, true_transaction_contents, 100
        )

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    def test_split_transactions_over_accounts_multiple_acc_cc(self, mock_product_to_accounting: Mock) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id, transaction.amount, transaction.created_at, Decimal("1.00")
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect

        accounting, leftover_amounts = split_transactions_over_accounts(transactions, completed_payments)
        assert len(leftover_amounts) == 0

        assert len(accounting) == sum(num_products) * 4
        self.assertAccounting(
            num_products, true_transactions, completed_payments, accounting, true_transaction_contents, 50
        )

    # TODO test disabled because of rounding issues
    # @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    # def test_split_transactions_over_accounts_multiple_acc_cc_odd_fee(self, mock_product_to_accounting: Mock) -> None:
    #     num_transactions = 5
    #     num_products = [i + 1 for i in range(num_transactions)]
    #     random.shuffle(num_products)
    #     amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]

    #     true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
    #     completed_payments: Dict[int, CompletedPayment] = {}
    #     for transaction in true_transactions.values():
    #         completed_payments[transaction.id] = CompletedPayment(
    #             transaction.id, transaction.amount, transaction.created_at, Decimal("1.23")
    #         )

    #     transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
    #     assert transactions
    #     assert len(transactions) == num_transactions

    #     product_to_accounting_instance = mock_product_to_accounting.return_value
    #     product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect

    #     accounting, leftover_amounts = split_transactions_over_accounts(transactions, completed_payments)
    #     assert len(leftover_amounts) == 0

    #     assert len(accounting) == sum(num_products) * 4
    #     self.assertAccounting(
    #         num_products, true_transactions, completed_payments, accounting, true_transaction_contents, 50
    #     )

    # TODO test disabled because of rounding issues
    # @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    # def test_split_transactions_over_accounts_odd_fractions(self, mock_product_to_accounting: Mock) -> None:
    #     num_transactions = 2
    #     num_products = [2 for i in range(num_transactions)]
    #     amounts = [Decimal("100") + Decimal("1.23") * Decimal(i) for i in range(num_transactions)]

    #     true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
    #     completed_payments: Dict[int, CompletedPayment] = {}
    #     for transaction in true_transactions.values():
    #       completed_payments[transaction.id] = CompletedPayment(
    #         transaction.id, transaction.amount, transaction.created_at, Decimal("1.23")
    #     )

    #     transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
    #     assert transactions
    #     assert len(transactions) == num_transactions

    #     product_to_accounting_instance = mock_product_to_accounting.return_value
    #     product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect

    #     accounting, leftover_amounts = split_transactions_over_accounts(transactions, completed_payments)
    #     assert len(leftover_amounts) == 2

    #     for tuple_key, leftover in leftover_amounts.items():
    #         assert leftover == pytest.approx(Decimal("-0.01"), abs=0.01)

    #     assert len(accounting) == sum(num_products) * 4
    #     self.assertAccounting(num_products, true_transactions, completed_payments, accounting, true_transaction_contents, 50)


class SplitTransactionsWithoutMockTest(ProductToAccountCostCenterTest):
    number_of_accounts = 1
    number_of_cost_centers = 1
    amounts = [
        Decimal("100.0") + Decimal("10.0") * Decimal(i)  # TODO make a test with odd fractions
        for i in range(ProductToAccountCostCenterTest.number_of_products)
    ]

    def test_split_transaction_over_accounts_no_mock(self) -> None:
        count = 2

        member = self.db.create_member()
        products = db_session.query(Product).all()

        total_amount = Decimal("0")
        for product in products:
            total_amount += Decimal(str(round(product.price, 2))) * Decimal(count)

        created = datetime(2023, 3, 1, tzinfo=timezone.utc)
        true_transaction = self.db.create_transaction(
            member_id=member.member_id, amount=total_amount, created_at=created
        )

        true_transaction_contents: Dict[int, TransactionContent] = {}
        for product in products:
            amount = product.price * count
            true_transaction_contents[product.id] = self.db.create_transaction_content(
                transaction_id=true_transaction.id, product_id=product.id, amount=amount, count=count
            )

        completed_payments: Dict[int, CompletedPayment] = {}
        completed_payments[true_transaction.id] = CompletedPayment(
            true_transaction.id,
            true_transaction.amount,
            true_transaction.created_at,
            Decimal("1.00"),  # TODO make a test with odd fees
        )

        transactions_from_db = db_session.query(Transaction).outerjoin(TransactionContent).all()
        transactions_with_accounting, leftover_amounts = split_transactions_over_accounts(
            transactions_from_db, completed_payments
        )
        transactions_with_accounting.sort(key=lambda x: ((x.account or "0"), (x.cost_center or "0")))

        prod_to_account = ProductToAccountCostCenter()
        found_amounts_sum: Dict[Tuple[int, AccountingEntryType], Decimal] = {}

        for product in products:
            accounts_for_product = prod_to_account.get_account_cost_center(product.id)
            accounts_for_product.sort(key=lambda x: ((x.account or "0"), (x.cost_center or "0")))

            for account_cost_center in accounts_for_product:
                for i, transaction_acc in enumerate(transactions_with_accounting):
                    if (
                        transaction_acc.account == account_cost_center.account
                        and transaction_acc.cost_center == account_cost_center.cost_center
                    ):
                        index = i
                        break
                transaction_acc = transactions_with_accounting.pop(index)

                transaction_fee = completed_payments[true_transaction.id].fee
                amount = Decimal(true_transaction_contents[product.id].amount)
                amount = amount if transaction_acc.type == AccountingEntryType.CREDIT else amount - transaction_fee
                true_ammount = amount * account_cost_center.fraction / Decimal(100)

                assert transaction_acc.amount == true_ammount
                key: Tuple[int, AccountingEntryType] = (product.id, account_cost_center.type)
                if key in found_amounts_sum:
                    found_amounts_sum[key] += true_ammount
                else:
                    found_amounts_sum[key] = true_ammount

                assert transaction_acc.account == account_cost_center.account
                assert transaction_acc.cost_center == account_cost_center.cost_center
                assert transaction_acc.type == account_cost_center.type
                assert transaction_acc.date == true_transaction.created_at

        assert len(transactions_with_accounting) == 0

        for key, amount in found_amounts_sum.items():
            if key[1] == AccountingEntryType.DEBIT:
                assert amount == true_transaction_contents[key[0]].amount - completed_payments[true_transaction.id].fee
            else:
                assert amount == true_transaction_contents[key[0]].amount
