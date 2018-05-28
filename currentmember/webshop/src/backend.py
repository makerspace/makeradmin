from flask import request, abort, jsonify, render_template
import service
from service import eprint, assert_get, SERVICE_USER_ID, route_helper
import stripe
from decimal import Decimal, Rounded, localcontext
from collections import namedtuple
from webshop_entities import category_entity, product_entity, transaction_entity, transaction_content_entity, product_action_entity, webshop_completed_actions
CartItem = namedtuple('CartItem', 'id count amount')

instance = service.create(name="Makerspace Webshop Backend", url="webshop", port=8000, version="1.0")

# Grab the database so that we can use it inside requests
db = instance.db

# TODO: Get from env
stripe.api_key = "sk_test_4CJly7zar1Ahq8bmKn1wk5Ya"
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
product_entity.add_routes(instance, "product")

category_entity.db = db
category_entity.add_routes(instance, "category")

transaction_entity.db = db
transaction_entity.add_routes(instance, "transaction")

transaction_content_entity.db = db
transaction_content_entity.add_routes(instance, "transaction_content")

product_action_entity.db = db
product_action_entity.add_routes(instance, "product_action")

webshop_completed_actions.db = db
webshop_completed_actions.add_routes(instance, "completed_actions")


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


@instance.route("member/<int:id>/transactions", methods=["GET"])
@route_helper
def member_transactions(id):
    transactions = transaction_entity.list("member_id=%s", id)
    for tr in transactions:
        tr["content"] = transaction_content_entity.list("transaction_id=%s", tr["id"])

    return transactions


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

    return total_amount, items


def stripe_payment(amount, token):
    # Ensure that the amount to pay is in whole cents (ören)
    # This shouldn't be able to fail as all products in the database have prices in cents, but you never know.
    stripe_amount = amount * stripe_currency_base
    if (stripe_amount % 1) != 0:
        raise Exception("Amount did not convert purely to cents: " + str(amount))

    # The amount is stored as a Decimal, convert it to an int
    stripe_amount = int(stripe_amount)

    try:
        charge = stripe.Charge.create(
            amount=stripe_amount,
            currency=currency,
            description='Example charge',
            source=token,
        )
        eprint(charge)
        return None
    except stripe.StripeError as e:
        eprint("Stripe Charge Failed")
        return jsonify({"status": str(e)}), 400
    except Exception as e:
        eprint("Stripe Charge Failed")
        eprint(e)
        return jsonify({"status": "Failed"}), 400


def send_receipt_email(member_id, transaction_id):
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


duplicatePurchaseRands = set()


@instance.route("pay", methods=["POST"])
def pay():
    data = request.get_json()
    if data is None:
        abort(400, "missing json")

    # The frontend will add a per-page random value to the request.
    # This will try to prevent duplicate payments due to sending the payment request twice
    duplicatePurchaseRand = assert_get(data, "duplicatePurchaseRand")
    if duplicatePurchaseRand in duplicatePurchaseRands:
        abort(400, "duplicate")

    member_id = int(assert_get(request.headers, "X-User-Id"))
    if member_id <= 0:
        abort(400, "Services and other special member IDs cannot purchase anything")

    total_amount, items = validate_payment(data["cart"], data["expectedSum"])

    token = assert_get(data, "stripeToken")
    error_response = stripe_payment(total_amount, token)
    if error_response is not None:
        return error_response

    duplicatePurchaseRands.add(duplicatePurchaseRand)
    transaction_id = transaction_entity.post({"member_id": member_id, "amount": total_amount})["id"]
    for item in items:
        transaction_content_entity.post({"transaction_id": transaction_id, "product_id": item.id, "count": item.count, "amount": item.amount})

    send_receipt_email(member_id, transaction_id)
    eprint("Payment complete. id: " + str(transaction_id))
    return jsonify({"status": "ok", "data": {"transaction_id": transaction_id}})


instance.serve_indefinitely()
