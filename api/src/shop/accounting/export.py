from datetime import datetime
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Sequence
from zoneinfo import ZoneInfo

from basic_types.enums import AccountingEntryType
from basic_types.time_period import TimePeriod
from membership.models import Member
from service.config import get_makerspace_local_timezone
from service.db import db_session
from service.error import InternalServerError

from shop.accounting.accounting import (
    AccountingError,
    ProductToAccountCostCenter,
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_amounts_over_accounts,
    split_transactions_over_accounts,
)
from shop.accounting.models import AccountingExport, Aggregation
from shop.accounting.sie_file import get_sie_string
from shop.accounting.verification import create_verificatons
from shop.completed_payment import CompletedPayment, CourseBookingPayment, get_completed_payments_from_stripe
from shop.models import (
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
)
from shop.shop_data import get_product_data_by_special_id

logger = getLogger("makeradmin")


# Value of the special_product_id metadata on the hidden product whose accounting settings
# decide which accounts and cost centers all course booking income is booked on.
COURSE_BOOKING_SPECIAL_PRODUCT_ID = "course_booking"


def transaction_fees_to_transaction_with_accounting(
    completed_payments: Dict[int, CompletedPayment],
    course_bookings: Sequence[CourseBookingPayment] = (),
) -> List[TransactionWithAccounting]:
    # Invariant: all fee entries share these two objects. Verifications are grouped on object
    # identity, so separate instances would split the fees over several rows for account 6573.
    account = TransactionAccount(account="6573", description="6573", id=0, display_order=1)
    cost_center = TransactionCostCenter(cost_center="GM", description="Föreningsgemensamt", id=0, display_order=1)

    def fee_entry(transaction_id: int | None, fee: Decimal, date: datetime) -> TransactionWithAccounting:
        return TransactionWithAccounting(
            transaction_id=transaction_id,
            product_id=None,
            amount=fee,
            date=date,
            account=account,
            cost_center=cost_center,
            type=AccountingEntryType.DEBIT,
        )

    amounts = [fee_entry(p.transaction_id, p.fee, p.charge_created) for p in completed_payments.values()]
    amounts.extend(fee_entry(None, booking.fee, booking.charge_created) for booking in course_bookings)
    return amounts


def course_bookings_to_transactions_with_accounting(
    course_bookings: Sequence[CourseBookingPayment],
) -> List[TransactionWithAccounting]:
    """Book course booking income on the accounts of the hidden course booking product.

    Course bookings are sold by a separate app and have no makeradmin transactions, so
    the stripe charges are the source of truth. Fees are not included, they are booked by
    [transaction_fees_to_transaction_with_accounting].

    Raises [AccountingError] if there are bookings but no product to take the accounts from.
    """
    if not course_bookings:
        return []

    product = get_product_data_by_special_id(COURSE_BOOKING_SPECIAL_PRODUCT_ID)
    if product is None:
        raise AccountingError(
            f"There are {len(course_bookings)} course bookings in the period, but no product to take their "
            f'accounting from. Create a hidden product with metadata {{"special_product_id": '
            f'"{COURSE_BOOKING_SPECIAL_PRODUCT_ID}"}} and set its accounts and cost centers.'
        )
    product_accounting = ProductToAccountCostCenter([product.id]).get_account_cost_center(product.id)

    entries: List[TransactionWithAccounting] = []
    for booking in course_bookings:
        booking_entries, _ = split_amounts_over_accounts(
            product_accounting,
            {
                AccountingEntryType.CREDIT: booking.amount,
                AccountingEntryType.DEBIT: booking.amount - booking.fee,
            },
            transaction_id=None,
            product_id=product.id,
            date=booking.charge_created,
        )
        entries.extend(booking_entries)
    return entries


def export_accounting(start_date: datetime, end_date: datetime, aggregation: Aggregation, signer: Member) -> str:
    utc_zone = ZoneInfo("UTC")
    logger.info(
        f"Exporting accounting from {start_date} ({start_date.astimezone(utc_zone)}) to {end_date} ({end_date.astimezone(utc_zone)}) with signer member number {signer.member_number}"
    )
    stripe_payments = get_completed_payments_from_stripe(start_date, end_date)
    completed_payments = stripe_payments.transactions
    course_bookings = stripe_payments.course_bookings
    transactions = (
        db_session.query(Transaction)
        .filter(
            Transaction.created_at >= start_date.astimezone(utc_zone),
            Transaction.created_at < end_date.astimezone(utc_zone),
            Transaction.status == Transaction.Status.completed,
            Transaction.amount != 0,  # Gifts have an amount of zero
        )
        .outerjoin(TransactionContent)
        .all()
    )

    for transaction in transactions:
        logger.info(f"Transaction: {transaction.id}")

    for payment in completed_payments.values():
        logger.info(f"Payment: {payment.transaction_id}")

    diff = diff_transactions_and_completed_payments(transactions, completed_payments)
    if len(diff) > 0:
        raise AccountingError(f"Transactions and completed payments do not match, {diff}")

    transactions_with_accounting, rounding_errors = split_transactions_over_accounts(transactions, completed_payments)

    transactions_with_accounting.extend(course_bookings_to_transactions_with_accounting(course_bookings))
    transactions_with_accounting.extend(
        transaction_fees_to_transaction_with_accounting(completed_payments, course_bookings)
    )
    group_by_period = TimePeriod(aggregation.value)  # aggregation is in fact a subset

    verifications = create_verificatons(transactions_with_accounting, group_by_period)
    logger.info(f"Verifications: {verifications}")

    return get_sie_string(verifications, start_date, end_date, f"{signer.firstname} {signer.lastname}")


def do_export(export: AccountingExport) -> None:
    if export.status not in (AccountingExport.Status.pending, AccountingExport.Status.failed):
        raise ValueError(f"Export with id {export.id} is not pending or failed")

    export.content = None
    export.status = AccountingExport.Status.pending

    zone = get_makerspace_local_timezone()
    start_dt = datetime.combine(export.start_date, datetime.min.time(), tzinfo=zone)
    end_dt = datetime.combine(export.end_date, datetime.min.time(), tzinfo=zone)

    try:
        accounting_info = export_accounting(start_dt, end_dt, export.aggregation, export.signer)
        export.content = accounting_info
        export.status = AccountingExport.Status.completed
    except Exception as e:
        export.content = str(e)
        export.status = AccountingExport.Status.failed
        logger.exception(f"Failed to export accounting for {export}")

    db_session.commit()


def do_export_in_thread(export_id: int) -> None:
    """Run the export with the given id on a background thread's own database session.

    Contract: the export row must be committed before the thread starts, as the thread's
    session cannot see uncommitted rows of the request's session.
    """
    try:
        export = db_session.get(AccountingExport, export_id)
        if export is None:
            raise ValueError(f"Export with id {export_id} not found")
        do_export(export)
    except Exception:
        logger.exception(f"Accounting export {export_id} crashed")
    finally:
        # db_session is thread-scoped; without remove() every export thread leaks a pooled connection.
        db_session.remove()
