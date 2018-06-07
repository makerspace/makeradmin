from flask import request, abort, jsonify, render_template
import service
from service import eprint, assert_get, SERVICE_USER_ID, route_helper
import stripe
import os
from decimal import Decimal, Rounded, localcontext
from collections import namedtuple
from webshop_entities import category_entity, product_entity, transaction_entity, transaction_content_entity, product_action_entity, webshop_completed_actions, membership_products, webshop_stripe_pending
from typing import Set

CartItem = namedtuple('CartItem', 'id count amount')

instance = service.create(name="Makerspace Webshop Backend", url="webshop", port=8000, version="1.0")

# Grab the database so that we can use it inside requests
db = instance.db

stripe.api_key = os.environ["STRIPE_PRIVATE_KEY"]
stripe_signing_secret = os.environ["STRIPE_SIGNING_SECRET"]

# All stripe calculations are done with cents (ören in Sweden)
stripe_currency_base = 100
currency = "sek"

# Add routes for getting, saving, deleting and listing products and categories
# They will be exposed at
# GET /path/to/service/product: lists all products
# POST /path/to/service/product: creates a product
# GET /path/to/service/product/id: retrieves a product
# PUT /path/to/service/product/id: updates a product
# DELETE /path/to/service/product/id: deletes a product
# E.g to update product with id 42 you would issue a PUT request to
# /path/to/service/product/42
product_entity.db = db
product_entity.add_routes(instance, "product", read_permission=None, write_permission="webshop_edit")

category_entity.db = db
category_entity.add_routes(instance, "category", read_permission=None, write_permission="webshop_edit")

product_action_entity.db = db
product_action_entity.add_routes(instance, "product_action", read_permission=None, write_permission="webshop_edit")

transaction_entity.db = db
transaction_entity.add_routes(instance, "transaction")

transaction_content_entity.db = db
transaction_content_entity.add_routes(instance, "transaction_content")

webshop_completed_actions.db = db
webshop_completed_actions.add_routes(instance, "completed_actions")

webshop_stripe_pending.db = db


@instance.route("pending_actions", methods=["GET"])
@route_helper
def pending_actions():
    '''
    Finds every item in a transaction and checks the actions it has, then checks to see if all those actions have been completed (and are not deleted).
    The actions that are valid for a transaction are precisely those that existed at the time the transaction was made. Therefore if an action is added to a product
    in the future, that action will *not* be retroactively applied to all existing transactions.
    '''

    with db.cursor() as cur:
        # Note webshop_completed_actions.content_id IS NULL makes this a check for all actions that are *not* in the webshop_completed_actions table (i.e not completed).
        cur.execute("""
            SELECT webshop_transaction_contents.id, webshop_transaction_contents.transaction_id, webshop_transaction_contents.product_id,
                webshop_transaction_contents.count, webshop_transaction_contents.amount, webshop_product_actions.value, webshop_actions.id, webshop_actions.name, webshop_transactions.member_id
            FROM webshop_transaction_contents
            INNER JOIN webshop_product_actions ON webshop_product_actions.product_id=webshop_transaction_contents.product_id
            LEFT JOIN webshop_completed_actions ON webshop_transaction_contents.id=webshop_completed_actions.content_id
            INNER JOIN webshop_actions ON webshop_actions.id=webshop_product_actions.action_id
            INNER JOIN webshop_transactions ON webshop_transactions.id=webshop_transaction_contents.transaction_id
            WHERE webshop_completed_actions.content_id IS NULL
            AND webshop.transactions.status='complete'
            AND webshop_transactions.created_at>webshop_product_actions.created_at
            AND (webshop_transactions.created_at<webshop_product_actions.deleted_at OR webshop_product_actions.deleted_at IS NULL)
            """)

        return [
            {
                "item": {
                    "id": v[0],
                    "transaction_id": v[1],
                    "product_id": v[2],
                    "count": v[3],
                    "amount": str(v[4]),
                    "action_value": v[5],
                },
                "action": {
                    "id": v[6],
                    "name": v[7],
                },
                "member_id": v[8],
            } for v in cur.fetchall()
        ]


@instance.route("transaction/<int:id>/content", methods=["GET"])
@route_helper
def transaction_contents(id):
    return transaction_content_entity.list("transaction_id=%s", id)


@instance.route("member/<int:id>/transactions", methods=["GET"], permission=None)
@route_helper
def member_history(id):
    '''
    Helper for listing the full transaction history of a member, with product info included.
    '''

    user_id = int(assert_get(request.headers, "X-User-Id"))
    if id != user_id:
        abort(403)

    # TODO: All these database lookups could probably be optimized
    transactions = transaction_entity.list("member_id=%s", id)
    transactions.reverse()
    for tr in transactions:
        items = transaction_content_entity.list("transaction_id=%s", tr["id"])
        for item in items:
            item["product"] = product_entity.get(item["product_id"])

        tr["content"] = items

    return transactions


def copy_dict(source, fields):
    return {key: source[key] for key in fields if key in source}


def send_new_member_email(member_id):
    r = instance.gateway.post("messages", {
        "recipients": [
            {
                "type": "member",
                "id": member_id
            },
        ],
        "message_type": "email",
        "subject": "Välkommen till Stockholm Makerspace",
        "body": render_template("new_member_email.html", frontend_url=instance.gateway.get_frontend_url)
    })

    if not r.ok:
        eprint("Failed to send new member email")
        eprint(r.text)


@instance.route("register", methods=["POST"], permission=None)
@route_helper
def register():
    ''' Register a new member.
        See frontend.py:register_member
    '''

    data = request.get_json()
    if data is None:
        abort(400, "missing json")

    products = membership_products(db)

    purchase = assert_get(data, "purchase")
    if len(purchase["cart"]) != 1:
        abort(400, "cart must contain exactly 1 item")
    item = purchase["cart"][0]
    if item["count"] != 1:
        abort(400, "exactly 1 item must be purchased")
    if item["id"] not in (p["id"] for p in products):
        abort(400, f"product {item['id']} is not one of the allowed ones")

    # Register the new member.
    # We need to copy the member info for security reasons.
    # Otherwise an attacker could inject evil inputs like for example the 'groups' field which is a list of groups the member should be added to.
    # It would be quite a security risk if the member could add itself to the admins group when registering.
    valid_member_fields = [
        "member_number", "email", "password", "firstname", "lastname", "civicregno", "company",
        "orgno", "address_street", "address_extra", "address_zipcode", "address_city", "address_country", "phone"
    ]
    member = copy_dict(data["member"], valid_member_fields)
    member["validate_only"] = True
    r = instance.gateway.post("membership/member", member)
    if not r.ok:
        # Ideally should just return r.text, but the helper code for routes screws that up a bit right now
        abort(r.status_code, r.json()["message"])

    member = r.json()["data"]

    # Construct the purchase object again, using user data is always risky
    purchase = {
        "cart": [
            {
                "id": item["id"],
                "count": 1
            }
        ],
        "expectedSum": purchase["expectedSum"],
        "stripeToken": purchase["stripeToken"],
        "duplicatePurchaseRand": purchase["duplicatePurchaseRand"],
    }

    try:
        member_id = member["member_id"]
        # Get a login token for the new user
        token = instance.gateway.post("oauth/force_token", {"user_id": member_id}).json()["access_token"]

        # Note this will throw if the payment failed
        payment_result = pay(member_id=member_id, data=purchase)
        # Add the token to the response so that the user can be logged in immediately
        payment_result["token"] = token

        send_new_member_email(member["member_id"])
        return payment_result
    except:
        # Something went wrong (possibly the payment didn't go through), so delete the member again
        r = instance.gateway.delete(f"membership/member/{member_id}")
        assert(r.ok)
        raise


@instance.route("stripe_callback", methods=["POST"])
@route_helper
def stripe_callback():
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
          payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return abort(400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return abort(400)

    eprint(f"Received stripe callback of type {event.type}")
    if event.type in ["source.chargeable", "source.failed", "source.canceled"]:
        source = event.data.object
        with db.cursor() as cur:
            cur.execute("SELECT transaction_id FROM webshop_transactions INNER JOIN webshop_stripe_pending ON webshop_transactions.id=webshop_stripe_pending.transaction_id WHERE webshop_stripe_pending.stripe_token=%s", (source.id,))
            transaction_id = cur.fetchone()
            if transaction_id is None:
                abort(400, f"no transaction exists for that token ({source.id})")

        if event.type == "source.chargeable":
            # Payment should happen now
            stripe_payment(transaction_id, source)
        else:
            # Payment failed
            tr = transaction_entity.get(transaction_id)
            tr["status"] = "failed"
            transaction_entity.put(tr, transaction_id)
            eprint("Marked transaction as failed")


def process_cart(cart):
    with db.cursor() as cur:
        prices = []
        multiples = []
        for item in cart:
            cur.execute("SELECT price,smallest_multiple FROM webshop_products WHERE id=%s AND deleted_at IS NULL", item["id"])
            tup = cur.fetchone()
            if tup is None:
                abort(400, "Item " + str(item["id"]) + " does not exist")
            price, smallest_multiple = tup
            if price < 0:
                abort(400, "Item seems to have a negatice price. Not allowing purchases that item just in case. Item: " + str(item["id"]))
            prices.append(price)
            multiples.append(smallest_multiple)

        items = []
        with localcontext() as ctx:
            ctx.clear_flags()

            for price, smallest_multiple, item in zip(prices, multiples, cart):
                count = int(item["count"])
                if count <= 0:
                    abort(400, "Can only buy positive amounts of item " + str(item["id"]))
                if (count % smallest_multiple) != 0:
                    abort(400, f"Can only buy item {item['id']} in multiples of {smallest_multiple}, found {count}")

                item_amount = price * count
                items.append(CartItem(item["id"], count, item_amount))

            total_amount = sum(item.amount for item in items)
            if ctx.flags[Rounded]:
                # This can possibly happen with huge values, I suppose they will be caught below anyway but it's good to catch in any case
                abort(400, "Rounding ocurred during price calculations")

    return total_amount, items


def validate_payment(cart, expected_amount):
    if len(cart) == 0:
        abort(400, "No items in cart")

    total_amount, items = process_cart(cart)

    # Ensure that the frontend hasn't calculated the amount to pay incorrectly
    if abs(total_amount - Decimal(expected_amount)) > Decimal("0.01"):
        abort(400, "Expected total amount to pay to be " + str(expected_amount) + " but the cart items actually sum to " + str(total_amount))

    if total_amount > 10000:
        abort(400, "Not allowing purchases above 10000 kr to avoid mistakes")

    # Assert that the amount can be converted to a valid stripe amount
    convert_to_stripe_amount(total_amount)

    return total_amount, items


def convert_to_stripe_amount(amount: Decimal):
    # Ensure that the amount to pay is in whole cents (ören)
    # This shouldn't be able to fail as all products in the database have prices in cents, but you never know.
    stripe_amount = amount * stripe_currency_base
    if (stripe_amount % 1) != 0:
        raise Exception("Amount did not convert purely to cents: " + str(amount))

    # The amount is stored as a Decimal, convert it to an int
    return int(stripe_amount)


def stripe_payment(transaction_id: int, token: str):
    transaction = transaction_entity.get(transaction_id)

    if transaction["status"] != "pending":
        raise Exception("To complete a payment, it must be currently pending")

    stripe_amount = convert_to_stripe_amount(Decimal(transaction["amount"]))

    try:
        charge = stripe.Charge.create(
            amount=stripe_amount,
            currency=currency,
            description='Example charge',
            source=token,
        )
        eprint(charge)
    except stripe.StripeError as e:
        eprint("Stripe Charge Failed")
        abort(400, str(e))
    except Exception as e:
        eprint("Stripe Charge Failed")
        eprint(e)
        abort(400, "failed")

    transaction["status"] = "completed"
    transaction_entity.put(transaction, transaction_id)

    send_receipt_email(transaction["member_id"], transaction_id)
    eprint("Payment complete. id: " + str(transaction_id))


def send_receipt_email(member_id: int, transaction_id: int):
    transaction = transaction_entity.get(transaction_id)
    items = transaction_content_entity.list("transaction_id=%s", transaction_id)
    products = [product_entity.get(item["product_id"]) for item in items]

    r = instance.gateway.post("messages", {
        "recipients": [
            {
                "type": "member",
                "id": member_id
            },
        ],
        "message_type": "email",
        "subject": "Kvitto - Stockholm Makerspace",
        "body": render_template("receipt_email.html", cart=zip(products,items), transaction=transaction, currency="kr", frontend_url=instance.gateway.get_frontend_url)
    })

    if not r.ok:
        eprint("Failed to send receipt email")
        eprint(r.text)


duplicatePurchaseRands: Set[int] = set()


@instance.route("pay", methods=["POST"], permission=None)
@route_helper
def pay_route():
    data = request.get_json()
    if data is None:
        abort(400, "missing json")

    member_id = int(assert_get(request.headers, "X-User-Id"))
    return pay(member_id, data)


def add_transaction_to_db(member_id: int, total_amount: Decimal, items):
    transaction_id = transaction_entity.post({"member_id": member_id, "amount": total_amount, "status": "pending"})["id"]
    for item in items:
        transaction_content_entity.post({"transaction_id": transaction_id, "product_id": item.id, "count": item.count, "amount": item.amount})
    return transaction_id


def create_stripe_source(transaction_id: int, card_source: str, total_amount: Decimal):
    stripe_amount = convert_to_stripe_amount(total_amount)
    eprint("Token: " + str(card_source))
    return stripe.Source.create(
        amount=stripe_amount,
        currency=currency,
        type='three_d_secure',
        three_d_secure={
            'card': card_source,
        },
        redirect={
            'return_url': instance.gateway.get_frontend_url(f"shop/receipt/{transaction_id}")
        },
    )


def pay(member_id, data):
    # The frontend will add a per-page random value to the request.
    # This will try to prevent duplicate payments due to sending the payment request twice
    duplicatePurchaseRand = assert_get(data, "duplicatePurchaseRand")
    if duplicatePurchaseRand in duplicatePurchaseRands:
        abort(400, "duplicate")

    if member_id <= 0:
        abort(400, "Services and other special member IDs cannot purchase anything")

    total_amount, items = validate_payment(data["cart"], data["expectedSum"])

    transaction_id = add_transaction_to_db(member_id, total_amount, items)
    card_source = assert_get(data, "stripeSource")

    source = create_stripe_source(transaction_id, card_source, total_amount)
    eprint(source)

    status = source.status
    if status == "pending":
        # Redirect the user to do the 3D secure confirmation step
        webshop_stripe_pending.post({ "transaction_id": transaction_id, "stripe_token": source.id })
        return { "redirect": source.redirect.url }
    elif status == "failed":
        # The card does not support 3D secure
        # Try a normal payment
        token = card_source
    elif status == "chargeable":
        # This can happen in some cases when 3D secure is sort of supported
        # but the user does not need to perform any steps for it.
        token = source
    elif status == "canceled" or status == "consumed":
        abort(500, f"Found unexpected stripe source status '{status}'")
    else:
        eprint(f"Unknown stripe source status '{status}'")
        abort(500, f"Unknown stripe source status '{status}'")

    stripe_payment(transaction_id, token)

    duplicatePurchaseRands.add(duplicatePurchaseRand)

    return {"transaction_id": transaction_id}


instance.serve_indefinitely()
