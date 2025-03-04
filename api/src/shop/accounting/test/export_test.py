from datetime import datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List
from unittest.mock import Mock, patch

import core
import membership
import shop
import shop.accounting
from basic_types.enums import AccountingEntryType
from basic_types.time_period import TimePeriod
from membership.models import Member
from service.db import db_session
from shop.accounting.export import (
    do_export,
    export_accounting,
    transaction_fees_to_transaction_with_accounting,
)
from shop.accounting.models import AccountingExport, Aggregation
from shop.completed_payment import CompletedPayment
from shop.models import (
    Product,
    ProductAccountsCostCenters,
    ProductCategory,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
)
from test_aid.test_base import FlaskTestBase

logger = getLogger("makeradmin")


class ExportTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models, shop.accounting.models]

    def setUp(self) -> None:
        self.member = self.db.create_member(firstname="Test", lastname="Testsson")

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
            assert transaction_fees[i].cost_center.cost_center == "FG"

    @patch("shop.accounting.export.export_accounting")
    def test_create_accounting_file(self, export_accounting: Mock) -> None:
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        accounting_info = "accounting string"
        export_accounting.return_value = accounting_info
        accounting_export = AccountingExport(
            signer_member_id=self.member.member_id,
            aggregation=Aggregation.month,
            start_date=start_date,
            end_date=end_date,
        )
        db_session.add(accounting_export)
        db_session.commit()

        do_export(accounting_export)

        self.assertEqual(accounting_export.status, AccountingExport.Status.completed)
        self.assertEqual(accounting_export.content, accounting_info)


class AccountingExportWithStripeMockTest(FlaskTestBase):
    models = [core.models, membership.models, shop.models]
    number_of_products = 3
    number_of_accounts = 2
    number_of_cost_centers = 2
    number_of_verifications = 2
    number_of_transactions = 3
    amounts = [Decimal("100.0") + Decimal("10.1") * Decimal(i) for i in range(number_of_products)]
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

        self.transaction_accounts: Dict[AccountingEntryType, List[TransactionAccount]] = {}
        self.transaction_cost_centers: Dict[AccountingEntryType, List[TransactionCostCenter]] = {}

        self.member = self.db.create_member(firstname="Test", lastname="Testsson")

        for type in AccountingEntryType:
            self.transaction_accounts[type] = []
            self.transaction_cost_centers[type] = []
            for i in range(self.number_of_accounts):
                acc = self.db.create_transaction_account(
                    account=f"account {type.value} {i}", description=f"account {i} {type.value}"
                )
                self.transaction_accounts[type].append(acc)
            for i in range(self.number_of_cost_centers):
                cc = self.db.create_transaction_cost_center(
                    cost_center=f"cost_center {type.value} {i}", description=f"cost_center {i} {type.value}"
                )
                self.transaction_cost_centers[type].append(cc)

        product_category = self.db.create_category()
        for i in range(self.number_of_products):
            product_price = self.amounts[i]
            product = self.db.create_product(category_id=product_category.id, price=product_price)
            fractions_left = {type: 100 for type in AccountingEntryType}
            for j in range(self.number_of_accounts):
                for k in range(self.number_of_cost_centers):
                    for type in AccountingEntryType:
                        added = False
                        fraction = round(100 / (self.number_of_accounts * (self.number_of_cost_centers + 1)))
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
        self.completed_payments: Dict[int, CompletedPayment] = {}

        for i in range(self.number_of_verifications):
            for j in range(self.number_of_transactions):
                total_amount = Decimal("0")
                for product in products:
                    if not (i != j and (i == product.id or j == product.id)):
                        total_amount += Decimal(str(round(product.price, 2))) * Decimal(self.count)

                created = datetime(2023, i + 1, j + 5, tzinfo=timezone.utc)
                transaction = self.db.create_transaction(
                    member_id=self.member.member_id, amount=total_amount, created_at=created
                )

                for product in products:
                    if not (i != j and (i == product.id or j == product.id)):
                        amount = product.price * self.count
                        self.db.create_transaction_content(
                            transaction_id=transaction.id, product_id=product.id, amount=amount, count=self.count
                        )

                self.completed_payments[transaction.id] = CompletedPayment(
                    transaction.id,
                    transaction.amount,
                    created,
                    self.transaction_fee,
                )

    @patch("shop.accounting.export.get_completed_payments_from_stripe")
    def test_export_accounting(self, get_payments_from_stripe: Mock) -> None:
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        ver_1_amounts = [Decimal("-1296.13"), Decimal("-265.47"), Decimal("1293.64"), Decimal("264.96")]
        ver_2_amounts = [Decimal("-1130.13"), Decimal("-231.47"), Decimal("1127.63"), Decimal("230.97")]
        ver_amounts = [ver_1_amounts, ver_2_amounts]

        get_payments_from_stripe.return_value = self.completed_payments

        sie_str = export_accounting(start_date, end_date, Aggregation.month, self.member)
        sie_rows = sie_str.split("\n")

        while True:
            row = sie_rows.pop(0)

            if row.startswith("#GEN"):
                assert datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y%m%d") in row
                assert self.member.firstname in row
                assert self.member.lastname in row

            if row.startswith("#DIM"):
                assert "Kostnadställe" in row

            if row.startswith("#VER"):
                break

        for i in range(1, self.number_of_verifications + 1):
            verification_row = sie_rows.pop(0) if i != 1 else row
            assert verification_row.startswith(f'#VER B {i} 2023{i:02d}01 "MakerAdmin"')
            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "{"

            transaction_row = sie_rows.pop(0)
            assert transaction_row.startswith(f'#TRANS 6573 {{1 "FG"}} 3.00 2023{i:02d}01')

            for j in range(4):
                transaction_row = sie_rows.pop(0)
                right_half = transaction_row.split("}")[1]
                amount_str = right_half.split("2023")[0]
                amount = Decimal(amount_str)
                assert amount == ver_amounts[i - 1][j]

            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "}"

        assert len(sie_rows) == 0
