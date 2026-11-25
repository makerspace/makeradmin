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
from shop.accounting.accounting import AccountingError
from shop.accounting.export import (
    COURSE_BOOKING_SPECIAL_PRODUCT_ID,
    course_bookings_to_transactions_with_accounting,
    do_export,
    export_accounting,
    transaction_fees_to_transaction_with_accounting,
)
from shop.accounting.models import AccountingExport, Aggregation
from shop.completed_payment import CompletedPayment, CourseBookingPayment, StripePayments
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
            assert transaction_fees[i].cost_center.cost_center == "GM"

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
        # The bulk deletes below bypass the session, so members of the previous test would
        # otherwise linger in the identity map and collide with the reused primary keys.
        db_session.expunge_all()
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

        get_payments_from_stripe.return_value = StripePayments(transactions=self.completed_payments, course_bookings=[])

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
            assert transaction_row.startswith(f'#TRANS 6573 {{1 "GM"}} 3.00 2023{i:02d}01')

            for j in range(4):
                transaction_row = sie_rows.pop(0)
                right_half = transaction_row.split("}")[1]
                amount_str = right_half.split("2023")[0]
                amount = Decimal(amount_str)
                assert amount == ver_amounts[i - 1][j]

            verification_row = sie_rows.pop(0)
            assert verification_row.strip() == "}"

        assert len(sie_rows) == 0

    def course_bookings(self) -> List[CourseBookingPayment]:
        created = datetime(2024, 3, 10, tzinfo=timezone.utc)
        return [
            CourseBookingPayment(
                booking_id="b1", amount=Decimal("150.00"), charge_created=created, fee=Decimal("4.50")
            ),
            # Fully refunded: no income, but the fee is still paid.
            CourseBookingPayment(booking_id="b2", amount=Decimal("0.00"), charge_created=created, fee=Decimal("3.00")),
        ]

    def create_course_booking_product(self) -> Product:
        product = self.db.create_product(
            product_metadata={"special_product_id": COURSE_BOOKING_SPECIAL_PRODUCT_ID}, show=False
        )
        for type in AccountingEntryType:
            self.db.create_product_account_cost_center(
                product_id=product.id,
                account_id=self.transaction_accounts[type][0].id,
                cost_center_id=None,
                type=type.value,
                fraction=100,
            )
        return product

    def test_course_bookings_are_booked_on_course_booking_product(self) -> None:
        self.create_course_booking_product()
        bookings = self.course_bookings()

        entries = course_bookings_to_transactions_with_accounting(bookings)
        entries.extend(transaction_fees_to_transaction_with_accounting({}, bookings))

        credit = [e for e in entries if e.type == AccountingEntryType.CREDIT]
        debit = [e for e in entries if e.type == AccountingEntryType.DEBIT]
        assert sum(e.amount for e in credit) == Decimal("150.00")
        assert sum(e.amount for e in debit) == Decimal("150.00")
        assert {e.account for e in credit} == {self.transaction_accounts[AccountingEntryType.CREDIT][0]}
        fees = [e for e in debit if e.account is not None and e.account.account == "6573"]
        assert sum(e.amount for e in fees) == Decimal("7.50")
        # Invariant: one shared fee account object, or the fees end up on several verification rows.
        assert len({id(e.account) for e in fees}) == 1

    def test_course_bookings_without_product_fail_export(self) -> None:
        with self.assertRaises(AccountingError) as context:
            course_bookings_to_transactions_with_accounting(self.course_bookings())
        assert COURSE_BOOKING_SPECIAL_PRODUCT_ID in str(context.exception)

    @patch("shop.accounting.export.get_completed_payments_from_stripe")
    def test_export_accounting_with_only_course_bookings(self, get_payments_from_stripe: Mock) -> None:
        self.create_course_booking_product()
        get_payments_from_stripe.return_value = StripePayments(transactions={}, course_bookings=self.course_bookings())

        sie_str = export_accounting(datetime(2024, 3, 1), datetime(2024, 4, 1), Aggregation.month, self.member)

        transaction_rows = [row.strip() for row in sie_str.split("\n") if row.strip().startswith("#TRANS")]
        assert len(transaction_rows) == 3
        assert transaction_rows[0].startswith('#TRANS 6573 {1 "GM"} 7.50 20240301')
        amounts = sorted(Decimal(row.split("}")[1].split("2024")[0]) for row in transaction_rows[1:])
        assert amounts == [Decimal("-150.00"), Decimal("142.50")]
