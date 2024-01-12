import random
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
from basic_types.enums import AccountingEntryType
from basic_types.time_period import TimePeriod, date_to_period
from membership.models import Member
from service.db import db_session
from shop.accounting.accounting import TransactionWithAccounting
from shop.accounting.export import export_accounting, transaction_fees_to_transaction_with_accounting
from shop.accounting.verification import Verification
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
            assert transaction_fees[i].account.account == "6573"
            assert transaction_fees[i].cost_center.cost_center == "Föreningsgemensamt"


class AccountingExportWithStripeMockTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]
    number_of_products = 2
    number_of_accounts = 2
    number_of_cost_centers = 2
    amounts = [
        Decimal("100.0") + Decimal("10.0") * Decimal(i)  # TODO make a test with odd fractions
        for i in range(number_of_products)
    ]
    transaction_fee = Decimal("1.00")
    count = 2

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Product).delete()
        db_session.query(ProductCategory).delete()
        db_session.query(Transaction).delete()
        db_session.query(TransactionContent).delete()
        db_session.query(TransactionAccount).delete()
        db_session.query(TransactionCostCenter).delete()
        db_session.query(ProductAccountsCostCenters).delete()

        random_scale = self.number_of_accounts * self.number_of_cost_centers / 2

        self.transaction_accounts: Dict[AccountingEntryType, List[TransactionAccount]] = {}
        self.transaction_cost_centers: Dict[AccountingEntryType, List[TransactionCostCenter]] = {}

        self.member = self.db.create_member()

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
                        max_fraction = min(fractions_left[type] / 2, 100 / random_scale)
                        fraction = random.randint(1, round(max_fraction))
                        if j > k:
                            self.db.create_product_account_cost_center(
                                product_id=product.id,
                                account_id=self.transaction_accounts[type][j].id,
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

        products = db_session.query(Product).all()
        total_amount = Decimal("0")
        for product in products:
            total_amount += Decimal(str(round(product.price, 2))) * Decimal(self.count)

        created = datetime(2023, 3, 1, tzinfo=timezone.utc)
        self.transaction = self.db.create_transaction(
            member_id=self.member.member_id, amount=total_amount, created_at=created
        )

        self.transaction_contents: Dict[int, TransactionContent] = {}
        for product in products:
            amount = product.price * self.count
            self.transaction_contents[product.id] = self.db.create_transaction_content(
                transaction_id=self.transaction.id, product_id=product.id, amount=amount, count=self.count
            )

        self.completed_payments: Dict[int, CompletedPayment] = {}
        self.completed_payments[self.transaction.id] = CompletedPayment(
            self.transaction.id,
            self.transaction.amount,
            self.transaction.created_at,
            self.transaction_fee,
        )

    @patch("shop.accounting.export.get_completed_payments_from_stripe")
    def test_export_accounting(self, get_payments_from_stripe: Mock) -> None:
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        # get_payments_from_stripe.return_value = self.completed_payments

        # logger.info(f"Completed payments: {self.completed_payments}")

        # sie_str = export_accounting(start_date, end_date, TimePeriod.Month, self.member)

        # logger.info(f"{sie_str}")

        # sie_rows = sie_str.split("\n")

        # # TODO assert more info about the header
        # while True:
        #     row = sie_rows.pop(0)

        #     if row.startswith("#GEN"):
        #         assert datetime.now().strftime("%Y%m%d") in row
        #         assert self.member.firstname in row
        #         assert self.member.lastname in row

        #     if row.startswith("#DIM"):
        #         assert "Kostnadställe" in row

        #     if row.startswith("#VER"):
        #         break

        # number_of_verifications = 1
        # number_of_transactions = 1
        # for i in range(1, number_of_verifications + 1):
        #     verification_row = sie_rows.pop(0) if i != 1 else row
        #     assert verification_row.startswith(f'#VER B {i} 2023{i:02d}01 "MakerAdmin"')
        #     verification_row = sie_rows.pop(0)
        #     assert verification_row.strip() == "{"

        #     for j in range(1, number_of_transactions + 1):
        #         transaction_row = sie_rows.pop(0)

        #         if j % 2 == 0:
        #             assert transaction_row.startswith(
        #                 f'#TRANS account{j} {{1 "cost_center{j}"}} -{Decimal("1000") + Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
        #             )
        #         else:
        #             assert transaction_row.startswith(
        #                 f'#TRANS account{j} {{1 "cost_center{j}"}} {Decimal(f"{i * j + j}")} 2023{i:02d}01 "MakerAdmin period 2023-{i:02d}"'
        #             )

        #     verification_row = sie_rows.pop(0)
        #     assert verification_row.strip() == "}"

        # assert len(sie_rows) == 0

        # assert False
