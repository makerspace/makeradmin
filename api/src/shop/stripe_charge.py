from datetime import date, datetime, timezone
from logging import getLogger
from typing import Dict, List, Never, Optional
from zoneinfo import ZoneInfo

import stripe
from service.error import EXCEPTION, InternalServerError
from stripe import CardError, InvalidRequestError, StripeError

from shop.models import Transaction
from shop.stripe_constants import CURRENCY, ChargeStatus, MakerspaceMetadataKeys
from shop.stripe_util import convert_to_stripe_amount, retry
from shop.transactions import PaymentFailed, payment_success

logger = getLogger("makeradmin")


def raise_from_stripe_invalid_request_error(e: InvalidRequestError) -> Never:
    if "Amount must convert to at least" in str(e) or "Amount must be at least" in str(e):
        raise PaymentFailed("Total amount too small total, least chargable amount is around 5 SEK.")

    raise PaymentFailed(log=f"stripe charge failed: {str(e)}", level=EXCEPTION)


def charge_transaction(transaction: Transaction, charge: stripe.Charge) -> None:
    if ChargeStatus(charge.status) != ChargeStatus.SUCCEEDED:
        raise InternalServerError(
            log=f"unexpected charge status '{charge.status}' for transaction {transaction.id} this should be handled"
        )

    payment_success(transaction)


def get_stripe_charges(start_date: datetime, end_date: datetime) -> List[stripe.Charge]:
    expand = ["data.balance_transaction", "data.payment_intent"]
    created = {
        "gte": int(start_date.astimezone(ZoneInfo("UTC")).timestamp()),
        "lt": int(end_date.astimezone(ZoneInfo("UTC")).timestamp()),
    }
    logger.info(f"Fetching stripe charges from {start_date} ({created['gte']}) to {end_date} ({created['lt']})")

    def get_charges() -> List[stripe.Charge]:
        stripe_charges = retry(lambda: stripe.Charge.list(limit=100, created=created, expand=expand))
        return list(stripe_charges.auto_paging_iter())

    return retry(get_charges)
