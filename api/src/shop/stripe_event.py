from logging import getLogger

import stripe
from stripe.error import SignatureVerificationError

from service.error import BadRequest, InternalServerError
from shop.models import Transaction
from shop.stripe_charge import charge_transaction, create_stripe_charge
from shop.stripe_constants import STRIPE_SIGNING_SECRET, Type, Subtype, SourceType
from shop.transactions import get_source_transaction, commit_fail_transaction, PaymentFailed

logger = getLogger('makeradmin')


class IgnoreEvent(Exception): pass


def get_pending_source_transaction(source_id):
    transaction = get_source_transaction(source_id)
    
    if not transaction:
        raise IgnoreEvent(f"no transaction exists for source ({source_id})")
    
    if transaction.status != Transaction.PENDING:
        raise IgnoreEvent(f"transaction {transaction.id} status is {transaction.status}, source event {source_id}")

    return transaction


def stripe_charge_event(subtype, event):
    charge = event.data.object

    transaction = get_pending_source_transaction(charge.source.id)

    if subtype == Subtype.SUCCEEDED:
        charge_transaction(transaction, charge)
        
    elif subtype == Subtype.FAILED:
        commit_fail_transaction(transaction)
        logger.info(f"charge failed for transaction {transaction.id}, {charge.failure_message}")
        
    elif subtype.startswith(Subtype.DISPUTE_PREFIX):
        pass
    
    elif subtype.startswith(Subtype.REFUND_PREFIX):
        pass


def stripe_source_event(subtype, event):
    source = event.data.object
    
    transaction = get_pending_source_transaction(source.id)

    if subtype == Subtype.CHARGABLE:

        if source.type == SourceType.THREE_D_SECURE:
            # Charge card and resolve transaction, don't fail transaction on errors as it may be resolved when we get
            # callback again.
            try:
                charge = create_stripe_charge(transaction, source.id)
            except PaymentFailed as e:
                logger.info(f"failing transaction {transaction.id}, permanent error when creating charge: {str(e)}")
                commit_fail_transaction(transaction)
            else:
                charge_transaction(transaction, charge)
        
        elif source.type == SourceType.CARD:
            # Non 3d secure cards should be charged synchronously in payment, not here.
            raise IgnoreEvent(f"transaction {transaction.id} source event of type card is handled synchronously")
        
        else:
            raise InternalServerError(log=f"unexpected source type '{source.type}'"
                                          f" when handling source event: {source}")
        
    elif subtype in (Subtype.FAILED, Subtype.CANCELED):
        logger.info(f"failing transaction {transaction.id} due to source event subtype {subtype}")
        commit_fail_transaction(transaction)
        
    else:
        raise IgnoreEvent(f"source event subtype {subtype} for transaction {transaction.id}")


def stripe_event(event):
    logger.info(f"got stripe event of type {event.type}")

    try:
        event_type, event_subtype = event.type.split('.', 1)
        if event_type == Type.SOURCE:
            stripe_source_event(event_subtype, event)
            
        elif event_type == Type.CHARGE:
            stripe_charge_event(event_subtype, event)
    
    except IgnoreEvent as e:
        logger.info(f"ignoring event, {str(e)}")


def stripe_callback(data, headers):
    """ Handle stripe event callback. In case of non 200 response stripe will send the same event again (retrying a
    few times), so the code is written to handle that. For example an error that can be assumed to be intermittent
    like a communication error with stripe will not fail or succeed a transaction but just leave it as is. """
    try:
        signature = headers['Stripe-Signature']
        event = stripe.Webhook.construct_event(data, signature, STRIPE_SIGNING_SECRET)
    except (KeyError, SignatureVerificationError) as e:
        raise BadRequest(log=f"failed to process stripe callback: {str(e)}")

    stripe_event(event)


def process_stripe_events(start=None, source_id=None, type=None):
    """ Used to make server fetch stripe events, used for testing since webhook is hard to use. """
    
    def event_filter(event):
        if not source_id:
            return True

        obj = event.data.object

        if source_id == obj.id:
            return True

        try:
            if source_id == obj.three_d_secure.card:
                return True
        except AttributeError:
            pass
            
        try:
            if source_id == obj.object.source.three_d_secure.card:
                return True
        except AttributeError:
            pass
        
        return False
    
    logger.info(f"getting stripe events with start={start}, source_id={source_id}, type={type}")
    events = list(filter(event_filter,
                         stripe.Event.list(created={'gte': start} if start else None,
                                           type=type)))
    event_count = len(events)
    logger.info(f"got {event_count} events")
    for event in events:
        stripe_event(event)
        
    return event_count




