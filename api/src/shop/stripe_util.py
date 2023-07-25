from datetime import datetime, timezone
from decimal import Decimal
import random
import time
from typing import Callable, Optional, TypeVar

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

def event_semantic_time(event: stripe.Event) -> datetime:
    '''
    This is the time when the event happens semantically. E.g. an invoice is created at exactly 00:00 on the first of the month.
    This may be different from the time when the event is created in Stripe. In particular, when using a test clock
    the event_created_time is still in real-time, but the event_semantic_time follows the test clock.

    Some events do not have a semantic time. In that case we fall back on the event's timestamp.
    '''
    obj = event['data']['object']
    return datetime.fromtimestamp(obj['created'] if 'created' in obj else event['created'], timezone.utc)

T = TypeVar('T')
MAX_TRIES = 10

def retry(f: Callable[[], T]) -> T:
    """Retries a stripe operation if it fails with a rate limit error."""
    its = 0
    while True:
        try:
            return f()
        except stripe.error.RateLimitError:
            its += 1
            if its > MAX_TRIES:
                raise
            # Retry.
            # Especially when starting a lot of parallel tests, we can get rate limit errors.
            time.sleep(1.0 * (1.0 + random.random()))
