from decimal import Decimal
from typing import Optional

from service.error import InternalServerError
from shop.stripe_constants import STRIPE_CURRENTY_BASE
import stripe

def convert_to_stripe_amount(amount: Decimal) -> int:
    """ Convert decimal amount to stripe amount and return it. Fails if amount is not even cents (ören). """
    stripe_amount = amount * STRIPE_CURRENTY_BASE
    if stripe_amount % 1 != 0:
        raise InternalServerError(message=f"The amount could not be converted to an even number of ören ({amount}).",
                                  log=f"Stripe amount not even number of ören, maybe some product has uneven ören.")

    return int(stripe_amount)
