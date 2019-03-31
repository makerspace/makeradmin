from logging import getLogger

import stripe
from stripe.error import SignatureVerificationError, InvalidRequestError, CardError, StripeError

from service.error import BadRequest, InternalServerError
from shop.models import Transaction
from shop.stripe_util import convert_to_stripe_amount
from shop.transactions import PaymentFailed
from shop.transactions import fail_transaction, get_source_transaction

logger = getLogger('makeradmin')


def test_stripe_source_event(data):
    event = stripe.Webhook.construct_event(data, "", STRIPE_SIGNING_SECRET, tolerance=1e9)
    event_type, event_subtype = event.type.split('.', 1)
    assert event_type == Type.SOURCE
    handle_stripe_source_callback(event_subtype, event)

# TODO Try to simplify code below.


def process_stripe_event(event):
    try:
        logger.info(f"processing stripe event of type {event.type}")
        
        # TODO Duplicate code, see stripe callback.
        (event_type, event_subtype) = tuple(event.type.split('.', 1))
        if event_type == Type.SOURCE:
            handle_stripe_source_callback(event_subtype, event)
            
        elif event_type == Type.CHARGE:
            # TODO Keep this in case syncronous transaction goes wrong?
            handle_stripe_charge_callback(event_subtype, event)
    except Exception as e:
        pass


def process_stripe_events(start=None, source_id=None, type=None):
    
    def event_filter(event):
        if not source_id:
            return True

        obj = event.data.object

        if source_id == obj.id:
            return True

        if source_id == obj.three_d_secure.card:
            return True
            
        if source_id == obj.object.source.three_d_secure.card:
            return True
        
        return False
    
    logger.info(f"getting stripe events with start={start}, source_id={source_id}, type={type}")
    events = list(filter(event_filter,
                         stripe.Event.list(created={'gte': start} if start else None,
                                           type=type)))
    event_count = len(events)
    logger.info(f"got {event_count} events")
    for event in events:
        logger.info(f"processing event: {event}")
        process_stripe_event(event)
        
    return event_count




