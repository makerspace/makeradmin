from logging import getLogger

from core import auth
from membership.views import member_entity
from service.error import BadRequest
from shop.api_schemas import validate_data, purchase_schema, register_schema
from shop.shop_data import get_membership_products
from shop.stripe_payment_intent import pay_with_stripe
from shop.transactions import create_transaction

logger = getLogger('makeradmin')


def make_purchase(member_id=None, purchase=None, activates_member=False):
    """ Pay using the data in purchase, the purchase structure should be validated according to schema.  """
    
    payment_method_id = purchase["stripe_payment_method_id"]

    transaction = create_transaction(member_id=member_id, purchase=purchase, activates_member=activates_member,
                                     stripe_reference_id=payment_method_id)

    action_info = pay_with_stripe(transaction, payment_method_id)

    return transaction, action_info
    
    
def pay(data, member_id):
    validate_data(purchase_schema, data or {})

    if member_id <= 0:
        raise BadRequest("You must be a member to purchase materials and tools.")
   
    # This will raise if the payment fails.
    transaction, action_info = make_purchase(member_id=member_id, purchase=data)
    
    return {
        'transaction_id': transaction.id,
        'action_info': action_info,
    }


def register(data, remote_addr, user_agent):
    
    validate_data(register_schema, data or {})

    products = get_membership_products()

    purchase = data['purchase']

    cart = purchase['cart']
    if len(cart) != 1:
        raise BadRequest(message="The purchase must contain exactly one item.")
        
    item = cart[0]
    if item['count'] != 1:
        raise BadRequest(message="The purchase must contain exactly one item.")
    
    product_id = item['id']
    if product_id not in (p['id'] for p in products):
        raise BadRequest(message=f"Not allowed to purchase the product with id {product_id} when registring.")

    # This will raise if the creation fails, if it succeeds it will commit the member.
    member_id = member_entity.create(data.get('member', {}))['member_id']

    # This will raise if the payment fails.
    transaction, action_info = make_purchase(member_id=member_id, purchase=purchase, activates_member=True)

    # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
    # the user will be logged in.
    token = auth.force_login(remote_addr, user_agent, member_id)['access_token']

    return {
        'transaction_id': transaction.id,
        'token': token,
        'action_info': action_info,
    }
