from logging import getLogger

import stripe

from flask import Flask
from stripe.error import InvalidRequestError, CardError, StripeError
from service.error import InternalServerError, EXCEPTION
#from shop.models import Transaction
#from shop.stripe_constants import CURRENCY, ChargeStatus
#from shop.stripe_util import convert_to_stripe_amount
#from shop.transactions import PaymentFailed, payment_success

stripe.api_key = 'sk_test_4QHS9UR02FMGKPqdjElznDRI'

logger = getLogger('makeradmin')



def create_stripe_checkout_session(data, member_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
      'price_data': {
        'currency': 'usd',
        'product_data': {
          'name': 'T-shirt',
        },
        'unit_amount': 2000,
      },
      'quantity': 1,
    }],
            mode='payment',
            success_url="https://makerspace.se",
            cancel_url="https://google.com",
        )
    except Exception as e:
        return str(e)

    return Flask.redirect(checkout_session.url, code=303)
