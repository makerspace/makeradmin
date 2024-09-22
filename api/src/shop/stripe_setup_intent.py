from dataclasses import dataclass
from enum import Enum
from typing import Optional

import stripe
from service.error import BadRequest, InternalServerError
from stripe import CardError, SetupIntent

from shop.stripe_constants import PaymentIntentNextActionType, SetupIntentStatus
from shop.stripe_payment_intent import PaymentAction
from shop.stripe_util import replace_default_payment_method
from shop.transactions import PaymentFailed


class SetupIntentResult(str, Enum):
    Success = "success"
    RequiresAction = "requires_action"
    Wait = "wait"
    Failed = "failed"


@dataclass
class SetupIntentFailed(Exception):
    type: SetupIntentResult
    action_info: Optional[PaymentAction]
    error: Optional[str] = None


def check_next_action(intent: SetupIntent) -> PaymentAction:
    """The payment_intent requires customer action to be confirmed. Create response to client"""
    next_action_type = PaymentIntentNextActionType(intent["next_action"]["type"])

    if next_action_type == PaymentIntentNextActionType.USE_STRIPE_SDK:
        return PaymentAction(type=PaymentIntentNextActionType.USE_STRIPE_SDK, client_secret=intent["client_secret"])

    elif next_action_type == PaymentIntentNextActionType.REDIRECT_TO_URL:
        raise InternalServerError(log=f"unexpected next_action type, {next_action_type}")

    else:
        raise PaymentFailed(log=f"unknown next_action type, {next_action_type}")


def handle_setup_intent(setup_intent: stripe.SetupIntent) -> None:
    while True:
        status = SetupIntentStatus(setup_intent["status"])
        if status == SetupIntentStatus.REQUIRES_PAYMENT_METHOD:
            # This can happen if the card was declined.
            # In that case the user will just have to try again.
            raise SetupIntentFailed(
                type=SetupIntentResult.Failed,
                error=setup_intent["last_setup_error"]["message"],
                action_info=None,
            )
        elif status == SetupIntentStatus.REQUIRES_CONFIRMATION:
            try:
                setup_intent = stripe.SetupIntent.confirm(setup_intent.id)
            except CardError as e:
                assert e.error is not None
                # This can happen if the card was declined in *some* cases.
                # In particular, it happens if you try to use a real card in a testing environment.
                raise SetupIntentFailed(
                    type=SetupIntentResult.Failed,
                    error=e.error.message,
                    action_info=None,
                )
            continue
        elif status == SetupIntentStatus.REQUIRES_ACTION:
            payment_action = check_next_action(setup_intent)
            raise SetupIntentFailed(
                type=SetupIntentResult.RequiresAction,
                action_info=payment_action,
                error=None,
            )
        elif status == SetupIntentStatus.PROCESSING:
            raise SetupIntentFailed(type=SetupIntentResult.Wait, action_info=None, error=None)
        elif status == SetupIntentStatus.SUCCEEDED:
            # Yay!

            # Mark this payment method as the customer's default payment method for the future.
            # The customer must have a default payment method so that invoices for a subscription can be charged.
            replace_default_payment_method(setup_intent["customer"], setup_intent["payment_method"])
            return
        elif status == SetupIntentStatus.CANCELED:
            raise BadRequest(message="The payment was canceled.")
        else:
            assert False, f"Unknown status {status}"
