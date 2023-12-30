from logging import getLogger

import stripe
from service.error import EXCEPTION, InternalServerError
from stripe import CardError, InvalidRequestError, StripeError

from shop.models import Transaction
from shop.stripe_constants import CURRENCY, ChargeStatus
from shop.stripe_util import convert_to_stripe_amount
from shop.transactions import PaymentFailed, payment_success

logger = getLogger("makeradmin")


def raise_from_stripe_invalid_request_error(e) -> None:
    if "Amount must convert to at least" in str(e) or "Amount must be at least" in str(e):
        raise PaymentFailed("Total amount too small total, least chargable amount is around 5 SEK.")

    raise PaymentFailed(log=f"stripe charge failed: {str(e)}", level=EXCEPTION)


def create_stripe_charge(transaction: Transaction, card_source_id: stripe.Source) -> stripe.Charge:
    if transaction.status != Transaction.PENDING:
        raise InternalServerError(
            f"unexpected status of transaction",
            log=f"transaction {transaction.id} has unexpected status {transaction.status}",
        )

    stripe_amount = convert_to_stripe_amount(transaction.amount)

    try:
        return stripe.Charge.create(
            amount=stripe_amount,
            currency=CURRENCY,
            description=f"charge for transaction id {transaction.id}",
            source=card_source_id,
        )
    except InvalidRequestError as e:
        raise_from_stripe_invalid_request_error(e)

    except CardError as e:
        error = e.json_body.get("error", {})
        raise PaymentFailed(message=error.get("message"), log=f"stripe charge failed: {str(error)}")

    except StripeError as e:
        raise InternalServerError(log=f"stripe charge failed (possibly temporarily): {str(e)}")


def charge_transaction(transaction: Transaction, charge: stripe.Charge) -> None:
    if ChargeStatus(charge.status) != ChargeStatus.SUCCEEDED:
        raise InternalServerError(
            log=f"unexpected charge status '{charge.status}' for transaction {transaction.id} "
            f"this should be handled"
        )

    payment_success(transaction)
