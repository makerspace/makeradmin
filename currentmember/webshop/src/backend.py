from flask import Flask, request, abort, jsonify
import service
from service import eprint, assert_get, SERVICE_USER_ID, route_helper
import stripe
from decimal import Decimal, Rounded, localcontext
from collections import namedtuple
from webshop_entities import category_entity, product_entity, transaction_entity, transaction_content_entity
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


@instance.route("transaction/<int:id>/content", methods=["GET"])
@route_helper
def transaction_contents(id):
    return transaction_content_entity.list("deleted_at IS NULL AND transaction_id=%s", id)


def process_cart(cart):
    with db.cursor() as cur:
        prices = []
        for item in cart:
            cur.execute("SELECT price FROM webshop_products WHERE id=%s AND deleted_at IS NULL", item["id"])
            price = cur.fetchone()
            if price is None:
                abort(400, "Item " + str(item["id"]) + " does not exist")
            if price[0] < 0:
                abort(400, "Item seems to have a negatice price. Not allowing purchases that item just in case. Item: " + str(item["id"]))
            prices.append(price[0])

        items = []
        with localcontext() as ctx:
            for price, item in zip(prices, cart):
                count = int(item["count"])
                if count <= 0:
                    abort(400, "Can only buy positive amounts of item " + str(item["id"]))

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


@instance.route("pay", methods=["POST"])
def pay():
    data = request.get_json()
    if data is None:
        abort(400, "missing json")

    user_id = assert_get(request.headers, "X-User-Id")
    if user_id == SERVICE_USER_ID:
        abort(400, "Services cannot purchase anything")

    total_amount, items = validate_payment(data["cart"], data["expectedSum"])

    token = assert_get(data, "stripeToken")
    error_response = stripe_payment(total_amount, token)
    if error_response is not None:
        return error_response

    transaction_id = transaction_entity.post({"user_id": user_id, "amount": total_amount})["id"]
    for item in items:
        transaction_content_entity.post({"transaction_id": transaction_id, "product_id": item.id, "count": item.count, "amount": item.amount})

    return jsonify({"status": "ok", "data": {"transaction_id": transaction_id}})


instance.serve_indefinitely()
