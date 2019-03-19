from decimal import Decimal
from logging import getLogger

import stripe
from stripe.error import SignatureVerificationError, InvalidRequestError, CardError, StripeError

from shop.transactions import PaymentFailed
from service.config import config, get_public_url
from service.db import db_session
from service.error import BadRequest, InternalServerError
from shop.api_schemas import STRIPE_3D_SECURE_NOT_SUPPORTED
from shop.models import Transaction, StripePending
from shop.transactions import fail_transaction, get_source_transaction, complete_transaction, handle_payment_success

logger = getLogger('makeradmin')


stripe.api_key = config.get("STRIPE_PRIVATE_KEY", log_value=False)


CURRENCY = "sek"

# All stripe calculations are done with cents (ören in Sweden)
STRIPE_CURRENTY_BASE = 100

STRIPE_SIGNING_SECRET = config.get("STRIPE_SIGNING_SECRET", log_value=False)


class Type:
    SOURCE = 'source'
    CARD = 'card'
    CHARGE = 'charge'


class Subtype:
    CHARGABLE = 'chargeable'
    FAILED = 'failed'
    CANCELED = 'canceled'
    SUCCEEDED = 'succeeded'
    DISPUTE_PREFIX = 'dispute'
    REFUND_PREFIX = 'refund'


class SourceType:
    THREE_D_SECURE = 'three_d_secure'
    CARD = 'card'


class SourceStatus:
    CHARGEABLE = 'chargeable'
    CONSUMED = 'consumed'
    FAILED = 'failed'
    PENDING = "pending"


class SourceRedirectStatus:
    PENDING = 'pending'
    NOT_REQUIRED = 'not_required'


class ChargeStatus:
    SUCCEDED = 'succeded'


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
        raise InternalServerError(f"unexpected status of transaction",
                                  log=f"transaction {transaction.id} has unexpected status {transaction.status}")
    
    stripe_amount = convert_to_stripe_amount(transaction.amount)
    
    try:
        return stripe.Charge.create(
            amount=stripe_amount,
            currency=CURRENCY,
            description=f'charge for transaction id {transaction.id}',
            source=card_source_id,
        )
    except InvalidRequestError as e:
        if "Amount must convert to at least" in str(e):
            raise PaymentFailed("paynebt too small total, least chargable amount is around 5 SEK")
        
        raise PaymentFailed(log=f"stripe charge failed: {str(e)}")
            
    except CardError as e:
        error = e.json_body.get('error', {})
        raise PaymentFailed(message=error.get("message"), log=f"stripe charge failed: {str(error)}")
        
    except StripeError as e:
        raise PaymentFailed(log=f"stripe charge failed: {str(e)}")
    
    except Exception as e:
        logger.exception("unhandled exception when creating stripe charge, this should be handled")
        raise
    
    
def create_3d_secure_source(amount, card_source_id, shop_redirect_url):
    try:
        return stripe.Source.create(
            amount=convert_to_stripe_amount(amount),
            currency=CURRENCY,
            type=SourceType.THREE_D_SECURE,
            three_d_secure={'card': card_source_id},
            redirect={'return_url': shop_redirect_url},
        )
    except InvalidRequestError as e:
        if "Amount must convert to at least" in str(e):
            raise PaymentFailed("paynebt too small total, least chargable amount is around 5 SEK")

        raise PaymentFailed(log=True)


def handle_card_source(transaction, card_source_id):
    """ This is a directly chargable card that should be handled syncronously. """
    
    # TODO How can this fail?
    card_source = stripe.Source.retrieve(card_source_id)
    
    assert card_source.type == Type.CARD
    assert card_source.card.three_d_secure == STRIPE_3D_SECURE_NOT_SUPPORTED

    try:
        if card_source.status == SourceStatus.CHARGEABLE:
            charge = create_stripe_charge(transaction, card_source_id)
            
            if charge.status == ChargeStatus.SUCCEDED:
                # Avoid delay of feedback to customer, could be skipped and handled when webhook is called.
                complete_transaction(transaction)
                return
            
            # TODO Test this, when can this happend?
            logger.warning(f"transaction {transaction.id} card source charge status {charge.status}"
                           f", not {ChargeStatus.SUCCEDED}, is this an error state?")
            
        if card_source.status == SourceStatus.FAILED:
            raise PaymentFailed()
        
        if card_source.status == SourceStatus.CONSUMED:
            # Not necessarily an error but shouldn't happen.
            # TODO Does this happend in real life? Maybe it is a bug?
            raise InternalServerError(f"stripe source already marked as {SourceStatus.CONSUMED}", log=True)
    
        raise InternalServerError(f"unknown stripe source status {card_source.status}, this is a bug", log=True)
    
    except (InternalServerError, PaymentFailed):
        # TODO Should we really fail transaction on internal server error?
        fail_transaction(transaction)
        raise


def handle_three_d_secure_source(transaction, card_source_id):
    """ This is a 3d secure card that should be handled asyncronously. """
    
    try:
        source = create_3d_secure_source(transaction.amount, card_source_id,
                                         get_public_url(f"/shop/receipt/{transaction.id}"))
        
        logger.info(f"created 3ds stripe source for transaction {transaction.id}, source id {source.id}")
        
        db_session.add(StripePending(transaction_id=transaction.id, stripe_token=source.id))
    
        if source.status in {SourceStatus.PENDING, SourceStatus.CHARGEABLE}:
            # Assert 3d secure is pending redirect.
            if source.redirect.status not in {SourceRedirectStatus.PENDING, SourceRedirectStatus.NOT_REQUIRED}:
                raise InternalServerError(log=f"unexpected value for source.redirect.status, {source.redirect.status}")
            
            # Assert 3d secure is pending redirect.
            if not source.redirect.url:
                raise InternalServerError(log=f"invalid value for source.redirect.url, {source.redirect.url}")
            
            # Redirect the user to do the 3D secure confirmation step.
            if source.redirect.status == SourceRedirectStatus.PENDING:
                return source.redirect.url
            
        if source.status == SourceStatus.FAILED:
            raise PaymentFailed()

        raise InternalServerError(log=f"unknown stripe source status {source.status}")
    
    except (InternalServerError, PaymentFailed):
        # TODO Should we really fail transaction on internal server error?
        fail_transaction(transaction)
        raise


def handle_stripe_source(transaction, card_source_id, card_3d_secure):
    """ Handle stripe source from payment request, see https://stripe.com/docs/sources/three-d-secure. Returns
    redirect url or None if no redirect is needed. """
    
    if card_3d_secure == STRIPE_3D_SECURE_NOT_SUPPORTED:
        handle_card_source(transaction, card_source_id)
        return None
        
    return handle_three_d_secure_source(transaction, card_source_id)


def handle_stripe_source_callback(subtype, event):
    if subtype not in (Subtype.CHARGABLE, Subtype.FAILED, Subtype.CANCELED):
        return
        
    source = event.data.object
    
    transaction = get_source_transaction(source.id)

    if not transaction:
        logger.info(f"no transaction exists for token ({source.id}), ignoring event (usually fine)")
        return
    
    if subtype == Subtype.CHARGABLE:
        # Asynchronous charge should only be initiated from a 3D Secure source.
        if source.type == SourceType.THREE_D_SECURE:
            # Charge should be created now.
            try:
                charge = create_stripe_charge(transaction, source.id)
                # TODO Why can't we complete the transaction here.
            except PaymentFailed as e:
                logger.exception(f"create_stripe_charge failed, source={source.id}, transaction_id={transaction.id}")
                # TODO Why not raise here?
        
        elif source.type == SourceType.CARD:
            # All 'card' type sources that should be charged are handled synchronously, not here.
            pass
        
        else:
            logger.warning(f'unexpected source type {source.type} in stripe webhook: {source}')
            
    else:
        logger.info(f"transaction {transaction.id} failed")
        fail_transaction(transaction)


def stripe_callback(data, headers):
    logger.info(f"stripe callback with headers: {headers}")

    headers['TODO_VALUE_ERROR']

    try:
        event = stripe.Webhook.construct_event(data, headers['Stripe-Signature'], STRIPE_SIGNING_SECRET)
    except (KeyError, SignatureVerificationError) as e:
        raise BadRequest(log=f"failed to process stripe callback: {str(e)}")

    logger.info(f"stripe callback of type: {event.type}")

    event_type, event_subtype = event.type.split('.', 1)
    if event_type == Type.SOURCE:
        handle_stripe_source_callback(event_subtype, event)
        
    elif event_type == Type.CHARGE:
        handle_stripe_charge_callback(event_subtype, event)


# TODO Try to simplify code below.


def handle_stripe_charge_callback(subtype, event):
    charge = event.data.object
    
    transaction = get_source_transaction(charge.source.id)
    if not transaction:
        logger.error(f"no transaction for source {charge.source.id},  charge id {charge.id}, subtype {subtype}")
        return
    
    if subtype == Subtype.SUCCEEDED:
        handle_payment_success(transaction)
        
    elif subtype == Subtype.FAILED:
        fail_transaction(transaction)
        logger.info(f"charge {charge.id} (transaction {transaction.id}) failed with message {charge.failure_message}")
        
    elif subtype.startswith(Subtype.DISPUTE_PREFIX):
        # todo: log disputes for display in admin frontend.
        pass
    
    elif subtype.startswith(Subtype.REFUND_PREFIX):
        # todo: log refund for display in admin frontend.
        # todo: option in frontend to roll back actions.
        pass


def process_stripe_event(event):
    try:
        logger.info(f"processing stripe event of type {event.type}")
        (event_type, event_subtype) = tuple(event.type.split('.', 1))
        if event_type == Type.SOURCE:
            handle_stripe_source_callback(event_subtype, event)
            
        elif event_type == Type.CHARGE:
            handle_stripe_charge_callback(event_subtype, event)
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





