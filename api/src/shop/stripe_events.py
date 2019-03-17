from decimal import Decimal
from logging import getLogger

import stripe
from stripe.error import SignatureVerificationError

from service.config import config
from service.db import db_session
from service.error import BadRequest, InternalServerError
from shop.email import send_new_member_email, send_receipt_email
from shop.models import PendingRegistration, Transaction
from shop.transactions import fail_transaction, get_source_transaction, complete_transaction

logger = getLogger('makeradmin')


# TODO Maybe rename file and put all stripe in it?


# All stripe calculations are done with cents (ören in Sweden)
STRIPE_CURRENTY_BASE = 100

STRIPE_SIGNING_SECRET = config.get("STRIPE_SIGNING_SECRET", log_value=False)

STRIPE_TYPE_SOURCE = 'source'
STRIPE_TYPE_CHARGE = 'charge'

STRIPE_SUBTYPE_CHARGABLE = 'chargeable'
STRIPE_SUBTYPE_FAILED = 'failed'
STRIPE_SUBTYPE_CANCELED = 'canceled'
STRIPE_SUBTYPE_SUCCEEDED = 'succeeded'
STRIPE_SUBTYPE_DISPUTE_PREFIX = 'dispute'
STRIPE_SUBTYPE_REFUND_PREFIX = 'refund'

STRIPE_SOURCE_TYPE_3D_SECURE = 'three_d_secure'

CURRENCY = "sek"


def convert_to_stripe_amount(amount: Decimal) -> int:
    """ Convert decimal amount to stripe amount and return it. Fails if amount is not even cents (ören). """
    stripe_amount = amount * STRIPE_CURRENTY_BASE
    if stripe_amount % 1 != 0:
        raise InternalServerError(message=f"The amount could not be converted to an even number of ören ({amount}).",
                                  log=f"Stripe amount not even number of ören, maybe some product has uneven ören.")

    return int(stripe_amount)


# TODO Compare calling code, very different exception handling.
def create_stripe_charge(transaction, card_source_id) -> stripe.Charge:

    if transaction.status != Transaction.PENDING:
        raise InternalServerError(f"Unexpected status of transaction.",
                                  log=f"Transaction {transaction.id} has unexpected status {transaction.status}.")

    stripe_amount = convert_to_stripe_amount(transaction.amount)

    return stripe.Charge.create(
        amount=stripe_amount,
        currency=CURRENCY,
        description=f'Charge for transaction id {transaction.id}.',
        source=card_source_id,
    )


# TODO This does not belong here, move it...
def activate_member(member):
    logger.info(f"activating member {member.id}")
    member.deleted_at = None
    db_session.add(member)
    db_session.flush()
    send_new_member_email(member)


# TODO This belongs in pay, but needs to be called from callback...
def handle_payment_success(transaction):
    complete_transaction(transaction)
    if transaction.status != Transaction.COMPLETED:
        # TODO Is this really needed?
        logger.error(f"wanted to complete transaction but marked as {transaction.status}")
        return
    
    # Check if this transaction is a new member registration.
    if db_session.query(PendingRegistration).filter(PendingRegistration.transaction_id == transaction.id).count():
        activate_member(transaction.member)
        
    logger.info(f"sending receipt email to member {transaction.member_id}, transaction {transaction.id} complete")
    send_receipt_email(transaction)


def stripe_handle_source_callback(subtype, event):
    if subtype not in [STRIPE_SUBTYPE_CHARGABLE, STRIPE_SUBTYPE_FAILED, STRIPE_SUBTYPE_CANCELED]:
        return
        
    source = event.data.object
    
    transaction = get_source_transaction(source.id)

    if not transaction:
        logger.info(f"no transaction exists for token ({source_id}), ignoring event (usually fine)")
        return
    
    if subtype == STRIPE_SUBTYPE_CHARGABLE:
        # Asynchronous charge should only be initiated from a 3D Secure source.
        if source.type == STRIPE_SOURCE_TYPE_3D_SECURE:
            # Payment should happen now.
            try:
                create_stripe_charge(transaction, source.id)
            except Exception as e:
                logger.exception(f"create_stripe_charge failed, source={source.id}, transaction_id={transaction.id}")
        
        elif source.type == 'card':
            # All 'card' type sources that should be charged are handled synchronously, not here.
            pass
        else:
            logger.warning(f'unexpected source type {source.type} in stripe webhook: {source}')
            
    else:
        logger.info(f"transaction {transaction.id} failed")
        fail_transaction(transaction)


def stripe_handle_charge_callback(subtype, event):
    charge = event.data.object
    
    transaction = get_source_transaction(charge.source.id)
    if not transaction:
        logger.error(f"no transaction for source {charge.source.id},  charge id {charge.id}, subtype {subtype}")
        return
    
    if subtype == STRIPE_SUBTYPE_SUCCEEDED:
        handle_payment_success(transaction)
        
    elif subtype == STRIPE_SUBTYPE_FAILED:
        fail_transaction(transaction)
        logger.info(f"charge {charge.id} (transaction {transaction.id}) failed with message {charge.failure_message}")
        
    elif subtype.startswith(STRIPE_SUBTYPE_DISPUTE_PREFIX):
        # todo: log disputes for display in admin frontend.
        pass
    
    elif subtype.startswith(STRIPE_SUBTYPE_REFUND_PREFIX):
        # todo: log refund for display in admin frontend.
        # todo: option in frontend to roll back actions.
        pass


def stripe_callback(data, headers):
    logger.info(f"stripe callback with headers: {headers}")

    try:
        event = stripe.Webhook.construct_event(data, headers['Stripe-Signature'], STRIPE_SIGNING_SECRET)
    except (ValueError, SignatureVerificationError) as e:
        raise BadRequest(log=f"failed to process stripe callback: {str(e)}")

    logger.info(f"stripe callback of type: {event.type}")

    event_type, event_subtype = event.type.split('.', 1)
    if event_type == STRIPE_TYPE_SOURCE:
        stripe_handle_source_callback(event_subtype, event)
    elif event_type == STRIPE_TYPE_CHARGE:
        stripe_handle_charge_callback(event_subtype, event)


def process_stripe_event(event):
    try:
        logger.info(f"processing stripe event of type {event.type}")
        (event_type, event_subtype) = tuple(event.type.split('.', 1))
        if event_type == STRIPE_TYPE_SOURCE:
            stripe_handle_source_callback(event_subtype, event)
            
        elif event_type == STRIPE_TYPE_CHARGE:
            stripe_handle_charge_callback(event_subtype, event)
    except Exception as e:
        pass


def process_stripe_events(start=None, source_id=None):
    logger.info(f"getting stripe events with start {start} and source_id {source_id}")
    events = stripe.Event.list(created={'gt': start} if start else None)
    logger.info(f"got {len(events)} events")
    for event in events.auto_paging_iter():
        obj = event.get('data', {}).get('object', {})
        if source_id and source_id in (obj.get('source', {}).get('id'), obj.get('id')) or not source_id:
            process_stripe_event(event)
        else:
            logger.info(f"skipping event, not matching source_id")
