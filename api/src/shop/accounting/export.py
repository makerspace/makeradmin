from datetime import datetime
from logging import getLogger
from typing import Dict, List

from basic_types.enums import AccountingEntryType
from basic_types.time_period import TimePeriod
from membership.models import Member
from service.config import get_makerspace_local_timezone
from service.db import db_session
from service.error import InternalServerError
from zoneinfo import ZoneInfo

from shop.accounting.accounting import (
    AccountingError,
    TransactionWithAccounting,
    diff_transactions_and_completed_payments,
    split_transactions_over_accounts,
)
from shop.accounting.models import AccountingExport, Aggregation
from shop.accounting.sie_file import get_sie_string
from shop.accounting.verification import create_verificatons
from shop.completed_payment import CompletedPayment, get_completed_payments_from_stripe
from shop.models import (
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
)

logger = getLogger("makeradmin")


def transaction_fees_to_transaction_with_accounting(
    completed_payments: Dict[int, CompletedPayment],
) -> List[TransactionWithAccounting]:
    amounts: List[TransactionWithAccounting] = []
    account = TransactionAccount(account="6573", description="6573", id=0, display_order=1)
    cost_center = TransactionCostCenter(cost_center="GM", description="Föreningsgemensamt", id=0, display_order=1)
    for payment in completed_payments.values():
        amounts.append(
            TransactionWithAccounting(
                transaction_id=payment.transaction_id,
                product_id=None,
                amount=payment.fee,
                date=payment.charge_created,
                account=account,
                cost_center=cost_center,
                type=AccountingEntryType.DEBIT,
            )
        )
    return amounts


def export_accounting(start_date: datetime, end_date: datetime, aggregation: Aggregation, signer: Member) -> str:
    utc_zone = ZoneInfo("UTC")
    logger.info(
        f"Exporting accounting from {start_date} ({start_date.astimezone(utc_zone)}) to {end_date} ({end_date.astimezone(utc_zone)}) with signer member number {signer.member_number}"
    )
    completed_payments = get_completed_payments_from_stripe(start_date, end_date)
    transactions = (
        db_session.query(Transaction)
        .filter(
            Transaction.created_at >= start_date.astimezone(utc_zone),
            Transaction.created_at < end_date.astimezone(utc_zone),
            Transaction.status == Transaction.Status.completed,
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

    transaction_fees = transaction_fees_to_transaction_with_accounting(completed_payments)
    transactions_with_accounting.extend(transaction_fees)
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
