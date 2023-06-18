from stripe import PaymentIntent, SetupIntent
from service.error import InternalServerError
from shop.stripe_constants import PaymentIntentNextActionType

from shop.stripe_payment_intent import PaymentAction
from shop.transactions import PaymentFailed


def check_next_action(intent: SetupIntent) -> PaymentAction:
    """ The payment_intent requires customer action to be confirmed. Create response to client"""
    next_action_type = PaymentIntentNextActionType(intent["next_action"]["type"])

    if next_action_type == PaymentIntentNextActionType.USE_STRIPE_SDK:
        return PaymentAction(type=PaymentIntentNextActionType.USE_STRIPE_SDK, client_secret=intent["client_secret"])
    
    elif next_action_type == PaymentIntentNextActionType.REDIRECT_TO_URL:
        raise InternalServerError(log=f"unexpected next_action type, {next_action_type}")

    else:
        raise PaymentFailed(log=f"unknown next_action type, {next_action_type}")