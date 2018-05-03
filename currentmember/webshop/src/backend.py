from flask import Flask, request, abort, jsonify, render_template
import service
from service import eprint, assert_get, SERVICE_USER_ID
import stripe
from decimal import Decimal, Rounded, localcontext
from datetime import datetime, timezone
from collections import namedtuple

CartItem = namedtuple('CartItem', 'id count amount')

with service.create(name="Makerspace Webshop Backend", url="webshop", port=8000, version="1.0") as instance:
    app = Flask(__name__)

    # Grab the database so that we can use it inside requests
    db = instance.db

    # TODO: Get from env
    stripe.api_key = "sk_test_4CJly7zar1Ahq8bmKn1wk5Ya"
    # All stripe calculations are done with cents (ören in Sweden)
    stripe_currency_base = 100
    currency = "sek"

    @app.route(instance.full_path("products"), methods=["GET"])
    def products():
        with db.cursor() as cur:
            cur.execute("SELECT name,description,unit,price FROM webshop_products")
            products = cur.fetchall()
            return jsonify({
                "status": "ok",
                "data": [
                    {
                        "name": item[0],
                        "description": item[1],
                        "unit": item[2],
                        "price": str(item[3]),
                    } for item in products
                ]
            })

    @app.route(instance.full_path("products/<int:id>"), methods=["GET"])
    def product(id):
        with db.cursor() as cur:
            cur.execute("SELECT name,description,unit,price FROM webshop_products WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                return jsonify({"status": "not found"}), 404

            return jsonify({
                "status": "ok",
                "data": {
                    "name": item[0],
                    "description": item[1],
                    "unit": item[2],
                    "price": str(item[3]),
                }
            })

    @app.route(instance.full_path("products/<int:id>"), methods=["PUT"])
    def add_product(id):
        with db.cursor() as cur:
            cur.execute("SELECT name,description,unit,price FROM webshop_products WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                return jsonify({"status": "not found"}), 404

            return jsonify({
                "status": "ok",
                "data": {
                    "name": item[0],
                    "description": item[1],
                    "unit": item[2],
                    "price": str(item[3]),
                }
            })

    @app.route(instance.full_path("products/<int:id>"), methods=["DELETE"])
    def delete_product(id):
        with db.cursor() as cur:
            cur.execute("DELETE name,description,unit,price FROM webshop_products WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                return jsonify({"status": "not found"}), 404

            return jsonify({
                "status": "ok",
                "data": {
                    "name": item[0],
                    "description": item[1],
                    "unit": item[2],
                    "price": str(item[3]),
                }
            })

    def process_cart(cart):
        with db.cursor() as cur:
            eprint(cart)

            prices = []
            for item in cart:
                cur.execute("SELECT price FROM webshop_products WHERE id=%s", item["id"])
                price = cur.fetchone()
                if price is None:
                    abort(400, "Item " + str(item["id"]) + " does not exist")
                if price[0] < 0:
                    abort(400, "Item seems to have a negatice price. Not allowing purchasing that item just in case. Item: " + str(item["id"]))
                prices.append(price[0])

            eprint(prices)

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
        if abs(total_amount - expected_amount) > Decimal("0.01"):
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

    @app.route(instance.full_path("pay"), methods=["POST"])
    def pay():
        user_id = assert_get(request.headers, "X-User-Id")
        if user_id == SERVICE_USER_ID:
            abort(400, "Services cannot purchase anything")

        data = request.get_json()
        if data is None:
            abort(400, "missing json")

        total_amount, items = validate_payment(data["cart"], data["expectedSum"])

        token = assert_get(data, "stripeToken")
        error_response = stripe_payment(total_amount, token)
        if error_response is not None:
            return error_response

        with db.cursor() as cur:
            cur.execute("INSERT INTO webshop_transactions (member_id,amount) VALUES(%s,%s,%s)", (user_id, total_amount))
            transaction_id = cur.lastrowid
            eprint(transaction_id)
            cur.executemany("INSERT INTO webshop_transaction_contents (transaction_id,product_id,count,amount) VALUES(%s,%s,%s,%s)",
                            [(transaction_id, item.id, item.count, item.amount) for item in items]
                            )

        return jsonify({"status": "ok", "data": {"transaction_id": transaction_id}})

    instance.serve_indefinitely(app)
