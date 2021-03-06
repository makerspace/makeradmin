from logging import getLogger
from time import sleep

import stripe
from stripe.error import InvalidRequestError, StripeError, CardError

from service.db import db_session
from service.error import InternalServerError, EXCEPTION, BadRequest
from shop.models import Transaction, StripePending
from shop.stripe_constants import PaymentIntentStatus, PaymentIntentNextActionType, CURRENCY
from shop.stripe_util import convert_to_stripe_amount
from shop.transactions import PaymentFailed, payment_success, get_source_transaction, commit_fail_transaction

logger = getLogger('makeradmin')


def raise_from_stripe_invalid_request_error(e):
    if "Amount must convert to at least" in str(e) or "Amount must be at least" in str(e):
        raise PaymentFailed("Total amount too small total, least chargable amount is around 5 SEK.")

    raise PaymentFailed(log=f"stripe charge failed: {str(e)}", level=EXCEPTION)


def capture_stripe_payment_intent(transaction, payment_intent):
    """ This is payment_intent is authorized and can be captured synchronously. """

    if transaction.status != Transaction.PENDING:
        raise InternalServerError(f"unexpected status of transaction",
                                  log=f"transaction {transaction.id} has unexpected status {transaction.status}")

    try:
        captured_intent = stripe.PaymentIntent.capture(
            payment_intent.id
        )

        complete_payment_intent_transaction(transaction, captured_intent)
    except InvalidRequestError as e:
        raise PaymentFailed(log=f"stripe capture payment_intent failed: {str(e)}", level=EXCEPTION)

    except StripeError as e:
        raise InternalServerError(log=f"stripe capture payment_intent failed (possibly temporarily): {str(e)}")


def create_action_required_response(transaction, payment_intent):
    """ The payment_intent requires customer action to be confirmed. Create response to client"""

    try:
        db_session.add(StripePending(transaction_id=transaction.id, stripe_token=payment_intent.id))

        if payment_intent.next_action.type == PaymentIntentNextActionType.USE_STRIPE_SDK:
            return dict(type=PaymentIntentNextActionType.USE_STRIPE_SDK,
                        client_secret=payment_intent.client_secret)
        
        elif payment_intent.next_action.type == PaymentIntentNextActionType.REDIRECT_TO_URL:
            raise InternalServerError(log=f"unexpected next_action type, {payment_intent.next_action.type}")

        else:
            raise PaymentFailed(log=f"unknown next_action type, {payment_intent.next_action.type}")

    except Exception:
        # Fail transaction on all known and unknown errors to be safe, we won't charge a failed transaction.
        commit_fail_transaction(transaction)
        logger.info(f"failing transaction {transaction.id}, due to error when processing 3ds card")
        raise


def complete_payment_intent_transaction(transaction, payment_intent):
    if payment_intent.status != PaymentIntentStatus.SUCCEEDED:
        raise InternalServerError(
            log=f"unexpected payment_intent status '{payment_intent.status}' for transaction {transaction.id} "
            f"this should be handled")

    if transaction.status == Transaction.PENDING:
        payment_success(transaction)


def create_client_response(transaction, payment_intent):
    
    if payment_intent.status == PaymentIntentStatus.REQUIRES_ACTION:
        """ Requires further action on client side. """
        if not payment_intent.next_action:
            raise InternalServerError(f"intent next_action is required but missing ({payment_intent.next_action})")
        return create_action_required_response(transaction, payment_intent)

    elif payment_intent.status == PaymentIntentStatus.REQUIRES_CONFIRMATION:
        confirmed_intent = stripe.PaymentIntent.confirm(payment_intent.id)
        assert confirmed_intent.status != PaymentIntentStatus.REQUIRES_CONFIRMATION
        return create_client_response(transaction, confirmed_intent)

    elif payment_intent.status == PaymentIntentStatus.SUCCEEDED:
        payment_success(transaction)
        logger.info(f"succeeded: payment for transaction {transaction.id}, payment_intent id {payment_intent.id}")
        return None

    elif payment_intent.status == PaymentIntentStatus.REQUIRES_PAYMENT_METHOD:
        commit_fail_transaction(transaction)
        logger.info(f"failed: payment for transaction {transaction.id}, payment_intent id {payment_intent.id}")
        raise BadRequest(log=f"payment_intent requires payment method, either no method provided or the payment failed")

    else:
        raise InternalServerError(
            log=f"unexpected stripe payment_intent status {payment_intent.status}, this is a bug")


def confirm_stripe_payment_intent(data):
    """ Called by client after payment_intent next_action has been handled """

    payment_intent_id = data.get("payment_intent_id", None)
    if not payment_intent_id:
        raise BadRequest("Missing required parameter 'payment_intent_id'")

    transaction = get_source_transaction(payment_intent_id)
    if not transaction:
        raise BadRequest(f"unknown payment_intent ({payment_intent_id})")

    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    assert payment_intent.status == PaymentIntentStatus.REQUIRES_CONFIRMATION

    try:
        action_info = create_client_response(transaction, payment_intent)
    except CardError as e:
        # Reason can be for example: 'Your card's security code is incorrect'.
        commit_fail_transaction(transaction)
        err = PaymentFailed(log=f"Payment failed: {str(e)}", level=EXCEPTION)
        err.message = e.user_message
        raise err

    return dict(transaction_id=transaction.id,
                action_info=action_info)


def pay_with_stripe(transaction, payment_method_id):
    """ Handle stripe payment, Returns dict containing data for further processing customer action or None. """

    try:
        payment_intent = stripe.PaymentIntent.create(
            payment_method=payment_method_id,
            amount=convert_to_stripe_amount(transaction.amount),
            currency=CURRENCY,
            description=f'charge for transaction id {transaction.id}',
            confirmation_method='manual',
            confirm=True,
        )

        logger.info(
            f"created stripe payment_intent for transaction {transaction.id}, payment_intent id {payment_intent.id}")

        return create_client_response(transaction, payment_intent)
    except InvalidRequestError as e:
        raise_from_stripe_invalid_request_error(e)


