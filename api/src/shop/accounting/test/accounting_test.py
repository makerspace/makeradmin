import random
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Any, Dict, List, Tuple
from unittest import TestCase
from unittest.mock import Mock, patch

import core
import membership
import shop
from basic_types.enums import AccountingEntryType
from membership.models import Member
from service.db import db_session
from service.error import InternalServerError
from shop.accounting.accounting import (
    AccountCostCenter,
    ProductToAccountCostCenter,
    RoundingErrorSource,
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_transaction_fee_over_transaction_contents,
    split_transactions_over_accounts,
)
from shop.models import (
    Product,
    ProductAccountsCostCenters,
    ProductCategory,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
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
        db_session.query(TransactionCostCenter).delete()
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
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostCenter).delete()
        db_session.query(ProductAccountsCostCenters).delete()

        self.transaction_accounts: Dict[AccountingEntryType, List[TransactionAccount]] = {}
        self.transaction_cost_centers: Dict[AccountingEntryType, List[TransactionCostCenter]] = {}

        for type in AccountingEntryType:
            self.transaction_accounts[type] = []
            self.transaction_cost_centers[type] = []
            for i in range(self.number_of_accounts):
                acc = self.db.create_transaction_account()
                self.transaction_accounts[type].append(acc)
            for i in range(self.number_of_cost_centers):
                cc = self.db.create_transaction_cost_center()
                self.transaction_cost_centers[type].append(cc)
            random.shuffle(self.transaction_accounts[type])
            random.shuffle(self.transaction_cost_centers[type])

        product_category = self.db.create_category()
        for i in range(self.number_of_products):
            product_price = self.amounts[i]
            product = self.db.create_product(category_id=product_category.id, price=product_price)
            fractions_left = {type: 100 for type in AccountingEntryType}
            for j in range(self.number_of_accounts):
                for k in range(self.number_of_cost_centers):
                    for type in AccountingEntryType:
                        added = False
                        fraction = round(100 / (self.number_of_accounts * self.number_of_cost_centers * 1.3))
                        if j > k:
                            self.db.create_product_account_cost_center(
                                product_id=product.id,
                                account_id=self.transaction_accounts[type][j].id,
                                cost_center_id=self.transaction_cost_centers[type][k].id,
                                type=type.value,
                                fraction=fraction,
                            )
                            added = True
                        elif j == k:
                            self.db.create_product_account_cost_center(
                                product_id=product.id,
                                account_id=None,
                                cost_center_id=self.transaction_cost_centers[type][k].id,
                                type=type.value,
                                fraction=fraction,
                            )
                            added = True
                        if added:
                            fractions_left[type] -= fraction
            # Adding the leftover fractions
            for type in AccountingEntryType:
                fraction = fractions_left[type]
                self.db.create_product_account_cost_center(
                    product_id=product.id,
                    account_id=self.transaction_accounts[type][0].id,
                    cost_center_id=None,
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
                .outerjoin(TransactionCostCenter, ProductAccountsCostCenters.cost_center)
                .filter(ProductAccountsCostCenters.product_id == product.id)
                .all()
            )
            accounting = prod_to_account.get_account_cost_center(product.id)
            assert len(accounting) == len(db_info)
            accounting.sort(
                key=lambda x: (
                    (x.account.account if x.account else "0"),
                    (x.cost_center.cost_center if x.cost_center else "0"),
                )
            )
            db_info.sort(key=custom_sort_key)

            for acc, product_info in zip(accounting, db_info):
                assert acc.fraction >= 1
                assert acc.fraction <= 100
                assert acc.fraction == product_info.fraction
                assert acc.type == AccountingEntryType(product_info.type)

                if product_info.account is None:
                    assert acc.account is None
                else:
                    assert acc.account == product_info.account
                if product_info.cost_center is None:
                    assert acc.cost_center is None
                else:
                    assert acc.cost_center == product_info.cost_center

    def test_product_to_accounting_outside_range_0(self) -> None:
        products = db_session.query(Product).all()
        self.db.create_product_account_cost_center(
            product_id=products[0].id,
            account_id=self.transaction_accounts[AccountingEntryType.CREDIT][0].id,
            cost_center_id=self.transaction_cost_centers[AccountingEntryType.CREDIT][0].id,
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
            account_id=self.transaction_accounts[AccountingEntryType.CREDIT][0].id,
            cost_center_id=self.transaction_cost_centers[AccountingEntryType.CREDIT][0].id,
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
            account_id=self.transaction_accounts[AccountingEntryType.CREDIT][0].id,
            cost_center_id=self.transaction_cost_centers[AccountingEntryType.CREDIT][0].id,
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


class SplitFeesTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostCenter).delete()

    def create_fake_data(
        self, num_products: int, amount: Decimal
    ) -> Tuple[Dict[int, Transaction], Dict[int, Dict[int, TransactionContent]]]:
        member = self.db.create_member()
        product_category = self.db.create_category()
        true_transaction_contents: Dict[int, Dict[int, TransactionContent]] = {}
        true_transactions: Dict[int, Transaction] = {}

        created = datetime(2023, 3, 1, tzinfo=timezone.utc)
        transaction = self.db.create_transaction(member_id=member.member_id, amount=amount, created_at=created)
        true_transactions[transaction.id] = transaction

        transaction_contents: Dict[int, TransactionContent] = {}
        price_left = amount
        for j in range(num_products):
            if j == num_products - 1:
                product_price = price_left
            else:
                product_price = (
                    Decimal(round(amount / num_products))
                    if j != 0
                    else Decimal(round(amount / num_products)) + Decimal("1.00")
                )
                price_left -= product_price
            product = self.db.create_product(id=j + 1, category_id=product_category.id, price=product_price)
            transaction_contents[product.id] = self.db.create_transaction_content(
                transaction_id=transaction.id, product_id=product.id, amount=product_price, count=1
            )
        true_transaction_contents[transaction.id] = transaction_contents
        return true_transactions, true_transaction_contents

    def test_split_transaction_fee_over_transaction_contents_odd_fee(self) -> None:
        num_products = 3
        amount = Decimal("100") + Decimal("10.11")
        true_fee = Decimal("1.23")

        true_transactions, true_transaction_contents = self.create_fake_data(num_products, amount)

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        transaction = transactions[0]
        split_fees, rounding_error = split_transaction_fee_over_transaction_contents(transaction, true_fee)
        assert rounding_error == Decimal("0.01")

        assert len(split_fees) == num_products
        split_sum = Decimal("0")

        first_content = transaction.contents.pop(0)
        for transaction_content in transaction.contents:
            true_split = round(Decimal(transaction_content.amount / transaction.amount) * true_fee, 2)
            assert split_fees[transaction_content.id] == true_split
            split_sum += true_split
        last_split_fee = split_fees[first_content.id]
        assert last_split_fee == true_fee - split_sum
        assert true_fee == split_sum + last_split_fee


class SplitTransactionsTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostCenter).delete()

    @staticmethod
    def assertAccounting(
        num_products: List[int],
        true_transactions: Dict[int, Transaction],
        accounting: List[TransactionWithAccounting],
        true_transaction_contents: Dict[int, Dict[int, TransactionContent]],
        transaction_fee: Decimal,
        fraction: int,
    ) -> None:
        num_entry_types_found: Dict[AccountingEntryType, int] = {type: 0 for type in AccountingEntryType}
        transaction_sums: Dict[Tuple[AccountingEntryType, int], Decimal] = {}

        for acc in accounting:
            product_id = acc.product_id
            transaction = true_transactions[acc.transaction_id]
            num_entry_types_found[acc.type] += 1

            amount = Decimal(str(round(true_transaction_contents[transaction.id][product_id].amount, 2)))
            amount = amount if acc.type == AccountingEntryType.CREDIT else amount - transaction_fee
            actual_amount = amount * Decimal(fraction) * Decimal("0.01")  # Multiply by 0.01 instead of dividing by 100

            assert acc.amount == actual_amount

            key = (acc.type, transaction.id)
            if key not in transaction_sums:
                transaction_sums[key] = acc.amount
            else:
                transaction_sums[key] += acc.amount

            assert transaction.created_at == acc.date
            if product_id == 1:
                assert acc.account is None
            else:
                assert acc.type.value + "_acc" + str(product_id) in acc.account.account
            if product_id == 2:
                assert acc.cost_center is None
            else:
                assert acc.type.value + "_cc" + str(product_id) in acc.cost_center.cost_center

        for transaction in true_transactions.values():
            for type in AccountingEntryType:
                fee = transaction_fee if type == AccountingEntryType.DEBIT else Decimal("0")
                key = (type, transaction.id)
                assert transaction.amount - (fee * len(transaction.contents)) == transaction_sums[key]

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
                    product_price = Decimal(round(amounts[i] / (num_products[i] + 1)))
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
            account_name = entry_type.value + "_acc" + str(product_id) + str(i)
            cost_center_name = entry_type.value + "_cc" + str(product_id) + str(i)
            account = TransactionAccount(id=i, account=account_name, description="", display_order=i)
            cost_center = TransactionCostCenter(id=i, cost_center=cost_center_name, description="", display_order=i)
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
            account_name = entry_type.value + "_acc" + str(product_id) + str(i)
            cost_center_name = entry_type.value + "_cc" + str(product_id) + str(i)
            account = TransactionAccount(id=i, account=account_name, description="", display_order=i)
            cost_center = TransactionCostCenter(id=i, cost_center=cost_center_name, description="", display_order=i)
            if product_id == 1:
                account = None
            elif product_id == 2:
                cost_center = None

            account_cost_center.append(AccountCostCenter(account, cost_center, 50, entry_type))
        return account_cost_center

    @staticmethod
    def get_split_fees_side_effect(transaction: Transaction, fee: Decimal) -> Tuple[Dict[int, Decimal], Decimal]:
        return ({content.id: Decimal("1.00") for content in transaction.contents}, Decimal("0.0"))

    @staticmethod
    def get_split_fees_side_effect_odd_fee(
        transaction: Transaction, fee: Decimal
    ) -> Tuple[Dict[int, Decimal], Decimal]:
        return ({content.id: Decimal("1.23") for content in transaction.contents}, Decimal("0.0"))

    @staticmethod
    def get_split_fees_side_effect_odd_fee_and_rounding_error(
        transaction: Transaction, fee: Decimal
    ) -> Tuple[Dict[int, Decimal], Decimal]:
        return ({content.id: Decimal("1.23") for content in transaction.contents}, Decimal("0.1"))

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    @patch("shop.accounting.accounting.split_transaction_fee_over_transaction_contents")
    def test_split_transactions_over_accounts_simple(
        self, split_fees_mock: Mock, mock_product_to_accounting: Mock
    ) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]
        transaction_fee = Decimal("1.00")

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id,
                transaction.amount,
                transaction.created_at,
                Decimal("1.00"),  # The fee is not used becaused of the mock
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        split_fees_mock.side_effect = self.get_split_fees_side_effect
        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect_one_acc_cc

        accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)
        assert len(rounding_errors) == 0

        self.assertAccounting(
            num_products,
            true_transactions,
            accounting,
            true_transaction_contents,
            transaction_fee,
            100,
        )

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    @patch("shop.accounting.accounting.split_transaction_fee_over_transaction_contents")
    def test_split_transactions_over_accounts_odd_fee(
        self, split_fees_mock: Mock, mock_product_to_accounting: Mock
    ) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]
        transaction_fee = Decimal("1.23")

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id,
                transaction.amount,
                transaction.created_at,
                Decimal("1.00"),  # The fee is not used becaused of the mock
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        split_fees_mock.side_effect = self.get_split_fees_side_effect_odd_fee
        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect_one_acc_cc

        accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)
        assert len(rounding_errors) == 0

        self.assertAccounting(
            num_products,
            true_transactions,
            accounting,
            true_transaction_contents,
            transaction_fee,
            100,
        )

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    @patch("shop.accounting.accounting.split_transaction_fee_over_transaction_contents")
    def test_split_transactions_over_accounts_rounding_error(
        self, split_fees_mock: Mock, mock_product_to_accounting: Mock
    ) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]
        transaction_fee = Decimal("1.23")

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id,
                transaction.amount,
                transaction.created_at,
                Decimal("1.00"),  # The fee is not used becaused of the mock
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        split_fees_mock.side_effect = self.get_split_fees_side_effect_odd_fee_and_rounding_error
        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect_one_acc_cc

        accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)
        assert len(rounding_errors) == num_transactions
        for error in rounding_errors:
            assert error.amount == Decimal("0.10")
            assert error.source == RoundingErrorSource.FEE_SPLIT

        self.assertAccounting(
            num_products, true_transactions, accounting, true_transaction_contents, transaction_fee, 100
        )

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    @patch("shop.accounting.accounting.split_transaction_fee_over_transaction_contents")
    def test_split_transactions_over_accounts_multiple_acc_cc(
        self, split_fees_mock: Mock, mock_product_to_accounting: Mock
    ) -> None:
        num_transactions = 5
        num_products = [i + 1 for i in range(num_transactions)]
        random.shuffle(num_products)
        amounts = [Decimal("100") + Decimal("10") * Decimal(i) for i in range(num_transactions)]
        transaction_fee = Decimal("1.00")

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id,
                transaction.amount,
                transaction.created_at,
                Decimal("1.00"),  # The fee is not used becaused of the mock
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        split_fees_mock.side_effect = self.get_split_fees_side_effect
        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect

        accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)
        assert len(rounding_errors) == 0

        self.assertAccounting(
            num_products, true_transactions, accounting, true_transaction_contents, transaction_fee, 50
        )

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    @patch("shop.accounting.accounting.split_transaction_fee_over_transaction_contents")
    def test_split_transactions_over_accounts_multiple_acc_cc_odd_fee(
        self, split_fees_mock: Mock, mock_product_to_accounting: Mock
    ) -> None:
        num_transactions = 1
        num_products = [2]
        amounts = [Decimal("100")]
        true_ammounts = [
            Decimal("16.5"),
            Decimal("15.89"),
            Decimal("16.5"),
            Decimal("15.88"),
            Decimal("33.5"),
            Decimal("32.89"),
            Decimal("33.5"),
            Decimal("32.88"),
        ]

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id,
                transaction.amount,
                transaction.created_at,
                Decimal("1.00"),  # The fee is not used becaused of the mock
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        split_fees_mock.side_effect = self.get_split_fees_side_effect_odd_fee
        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect

        accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)

        assert len(accounting) == sum(num_products) * 4
        for i, acc in enumerate(accounting):
            assert acc.amount == true_ammounts[i]

        assert len(rounding_errors) == 2
        for error in rounding_errors:
            assert error.amount == Decimal("0.01")
            assert error.source == RoundingErrorSource.TRANSACTION_SPLIT
            assert error.type == AccountingEntryType.DEBIT

    @patch("shop.accounting.accounting.ProductToAccountCostCenter")
    @patch("shop.accounting.accounting.split_transaction_fee_over_transaction_contents")
    def test_split_transactions_over_accounts_odd_fractions(
        self, split_fees_mock: Mock, mock_product_to_accounting: Mock
    ) -> None:
        num_transactions = 1
        num_products = [2]
        amounts = [Decimal("100.11")]
        true_ammounts = [
            Decimal("16.5"),
            Decimal("15.89"),
            Decimal("16.5"),
            Decimal("15.88"),
            Decimal("33.55"),
            Decimal("32.94"),
            Decimal("33.56"),
            Decimal("32.94"),
        ]

        true_transactions, true_transaction_contents = self.create_fake_data(num_transactions, num_products, amounts)
        completed_payments: Dict[int, CompletedPayment] = {}
        for transaction in true_transactions.values():
            completed_payments[transaction.id] = CompletedPayment(
                transaction.id, transaction.amount, transaction.created_at, Decimal("1.23")
            )

        transactions = db_session.query(Transaction).outerjoin(TransactionContent).all()
        assert transactions
        assert len(transactions) == num_transactions

        split_fees_mock.side_effect = self.get_split_fees_side_effect_odd_fee
        product_to_accounting_instance = mock_product_to_accounting.return_value
        product_to_accounting_instance.get_account_cost_center.side_effect = self.get_accounting_side_effect

        accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)

        assert len(accounting) == sum(num_products) * 4
        for i, acc in enumerate(accounting):
            assert acc.amount == true_ammounts[i]

        assert len(rounding_errors) == 2

        assert rounding_errors[0].amount == Decimal("0.01")
        assert rounding_errors[0].source == RoundingErrorSource.TRANSACTION_SPLIT
        assert rounding_errors[0].type == AccountingEntryType.DEBIT

        assert rounding_errors[1].amount == Decimal("-0.01")
        assert rounding_errors[1].source == RoundingErrorSource.TRANSACTION_SPLIT
        assert rounding_errors[1].type == AccountingEntryType.CREDIT
