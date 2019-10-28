from logging import getLogger

import stripe
from stripe.error import InvalidRequestError

from service.config import get_public_url
from service.db import db_session
from service.error import InternalServerError
from shop.api_schemas import STRIPE_3D_SECURE_NOT_SUPPORTED
from shop.models import StripePending
from shop.stripe_charge import raise_from_stripe_invalid_request_error, create_stripe_charge, charge_transaction
from shop.stripe_constants import Type, CURRENCY, SourceType, SourceStatus, SourceRedirectStatus
from shop.stripe_util import convert_to_stripe_amount
from shop.transactions import PaymentFailed, commit_fail_transaction

logger = getLogger('makeradmin')


def pay_with_card(transaction, card_source_id):
    """ This is a directly chargable card that should be handled syncronously. """
    
    try:
        card_source = stripe.Source.retrieve(card_source_id)
    
        assert card_source.type == Type.CARD
        assert card_source.card.three_d_secure == STRIPE_3D_SECURE_NOT_SUPPORTED

        if card_source.status == SourceStatus.CHARGEABLE:
            charge = create_stripe_charge(transaction, card_source_id)
            
        elif card_source.status == SourceStatus.FAILED:
            raise PaymentFailed(log=f"payment failed: {card_source}")
        
        elif card_source.status == SourceStatus.CONSUMED:
            raise InternalServerError(log=f"stripe source already marked as {SourceStatus.CONSUMED}")
    
        else:
            raise InternalServerError(log=f"unknown stripe source status {card_source.status}, this is a bug")
    
    except Exception as e:
        # Fail on all errors as we can't recover transaction when using synchronous card payments as we ignore the
        # card source callbacks.
        commit_fail_transaction(transaction)
        logger.info(f"failing transaction {transaction.id}, due to error when processing card")
        raise

    charge_transaction(transaction, charge)


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
        raise_from_stripe_invalid_request_error(e)


def pay_with_3d_secure_card(transaction, card_source_id):
    """ This is a 3d secure card that needs to handled asyncronously. """
    
    try:
        source = create_3d_secure_source(transaction.amount, card_source_id,
                                         get_public_url(f"/shop/receipt/{transaction.id}"))
        
        logger.info(f"created 3ds stripe source for transaction {transaction.id}, source id {source.id}")
        
        db_session.add(StripePending(transaction_id=transaction.id, stripe_token=source.id))
        
        if source.status in (SourceStatus.PENDING, SourceStatus.CHARGEABLE):
            # Redirect the user to do the 3D secure confirmation step.
            if source.redirect.status == SourceRedirectStatus.PENDING:
                if not source.redirect.url:
                    raise PaymentFailed(log=f"empty source.redirect.url")

                return source.redirect.url

            # Assert 3d secure is pending redirect.
            if source.redirect.status == SourceRedirectStatus.NOT_REQUIRED:
                return None
            
        if source.status == SourceStatus.FAILED:
            raise PaymentFailed()

        raise PaymentFailed(log=f"unknown stripe source status '{source.status}'"
                                f", source redirect status '{source.redirect.status}'")
    
    except Exception:
        # Fail transaction on all known and unknown errors to be safe, we won't charge a failed transaction.
        commit_fail_transaction(transaction)
        logger.info(f"failing transaction {transaction.id}, due to error when processing 3ds card")
        raise


def pay_with_stripe_card(transaction, card_source_id, card_3d_secure):
    """ Handle stripe card, see https://stripe.com/docs/sources/three-d-secure, the card is charged immediatly if it
    does not support 3d secure. Non 3d secure cards are very nice in testing because they do not require stripe
    webhooks but it is not used much in reality. Returns redirect url for 3d secure or none. """
    
    if card_3d_secure == STRIPE_3D_SECURE_NOT_SUPPORTED:
        pay_with_card(transaction, card_source_id)
        return None
    
    return pay_with_3d_secure_card(transaction, card_source_id)
