from flask import request, abort, jsonify, render_template
import service
from service import eprint, assert_get, SERVICE_USER_ID, route_helper, BackendException, format_datetime
import stripe
import os
from decimal import Decimal, Rounded, localcontext
from collections import namedtuple
from webshop_entities import category_entity, product_entity, action_entity, transaction_entity, transaction_content_entity, product_action_entity, membership_products, webshop_stripe_pending, webshop_pending_registrations, webshop_transaction_actions
from typing import Set, List, Dict, Any, NamedTuple, Tuple, Optional


class CartItem(NamedTuple):
    id: int
    count: int
    amount: Decimal


# Errors

def TooSmallAmount():
    return BackendException(tag="TooSmallAmount", sv="För litet belopp. Det minsta beloppet som kan handlas för är 50 cent (ca 5 kr).", en=None)


def TooLargeAmount(threshold: int):
    return BackendException(
        tag="TooLargeAmount",
        sv=f"Köp för över {threshold} kr är inte tillåtna för att undvika misstag. Behöver du köpa för så mycket, dela upp köpet i mindre delar.",
        en=f"Not allowing purchases above {threshold} kr to avoid mistakes."
    )


def NonMatchingSums(expected_sum, actual_sum):
    return BackendException(
        tag="NonMatchingSums",
        sv="Den förväntade summan att betala var " + str(expected_amount) + ", men produkterna i varukorgen kostar egentligen totalt " + str(total_amount) + ".",
        en="Expected total amount to pay to be " + str(expected_amount) + " but the cart items actually sum to " + str(total_amount) + "."
    )


def NotMember():
    return BackendException(
        tag="NotMember",
        sv="Du måste vara en medlem för att kunna köpa material och verktyg.",
        en="You must be a member to purchase materials and tools."
    )


def DuplicateTransaction():
    return BackendException(tag="DuplicateTransaction", sv="Du har redan gjort en betalning för detta.", en=None)


def MissingJson():
    return BackendException(tag="MissingJson", sv="Ingen json data skickades med anropet. Detta ser ut som en bugg.", en=None)


def NotPurelyCents(value):
    return BackendException(tag="NotPurelyCents", sv=f"Beloppet kunde inte konverteras till ett helt antal ören ({str(value)}).", en=None)


def NotAllowedToPurchase(product):
    return BackendException(tag="NotAllowedToPurchase", sv=f"Det är inte tillåtet att köpa produkten med id {product['id']}.", en=None)


def CartMustContainNItems(n: int):
    return BackendException(tag="CartMustContainNItems", sv=f"Köpet måste innehålla exakt {n} sak.", en=None)


def NonNegativeItemCount(item):
    return BackendException(
        tag="NonNegativeItemCount",
        sv=f"Kan endast köpa ett positivt antal av produkt {item}.",
        en=f"Can only buy positive amounts of item {item}."
    )


def InvalidItemCountMultiple(item, smallest_multiple, count):
    return BackendException(
        tag="InvalidItemCountMultiple",
        sv=f"Produkten {item} kan endast köpas i multipler av {smallest_multiple}, i varukorgen så fanns {count} enheter.",
        en=f"Can only buy item {item} in multiples of {smallest_multiple}, found {count}."
    )


def RoundingError():
    return BackendException(
        tag="RoundingError",
        sv="Ett avrundningsfel skedde när priset skulle beräknas.",
        en="Rounding ocurred during price calculations."
    )


def EmptyCart():
    return BackendException(
        tag="EmptyCart",
        sv="Inga produkter i varukorgen.",
        en="No items in cart."
    )


def NoSuchItem(item: str):
    return BackendException(
        tag="NoSuchItem",
        sv=f"Produkten {item} finns inte.",
        en=f"Item {item} does not exist."
    )


def PaymentFailed(error: str = None):
    if error is not None:
        return BackendException(
            tag="PaymentFailed",
            sv=f"Betalningen misslyckades, stripe säger {error}.",
            en=f"Payment failed, stripe says {error}."
        )
    else:
        return BackendException(
            tag="PaymentFailed",
            sv=f"Betalningen misslyckades.",
            en=f"Payment failed."
        )


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

action_entity.db = db
action_entity.add_routes(instance, "action", read_permission=None, write_permission="webshop_edit")

product_action_entity.db = db
product_action_entity.add_routes(instance, "product_action", read_permission=None, write_permission="webshop_edit")

transaction_entity.db = db
transaction_entity.add_routes(instance, "transaction", read_permission="webshop")

transaction_content_entity.db = db
transaction_content_entity.add_routes(instance, "transaction_content", read_permission="webshop")

webshop_transaction_actions.db = db
webshop_transaction_actions.add_routes(instance, "transaction_action")

webshop_pending_registrations.db = db

webshop_stripe_pending.db = db


@instance.route("pending_actions", methods=["GET"])
@route_helper
def pending_actions() -> List[Dict[str,Any]]:
    '''
    Finds every item in a transaction and checks the actions it has, then checks to see if all those actions have been completed (and are not deleted).
    The actions that are valid for a transaction are precisely those that existed at the time the transaction was made. Therefore if an action is added to a product
    in the future, that action will *not* be retroactively applied to all existing transactions.
    '''

    with db.cursor() as cur:
        cur.execute("""
            SELECT webshop_transaction_contents.id, webshop_transaction_contents.transaction_id, webshop_transaction_contents.product_id, webshop_transaction_contents.count,
                webshop_transaction_contents.amount, webshop_transaction_actions.value,
                webshop_actions.id, webshop_actions.name,
                webshop_transactions.member_id,
                webshop_transaction_actions.id
            FROM webshop_transaction_actions
            INNER JOIN webshop_actions              ON webshop_transaction_actions.action_id      = webshop_actions.id
            INNER JOIN webshop_transaction_contents ON webshop_transaction_actions.content_id     = webshop_transaction_contents.id
            INNER JOIN webshop_transactions         ON webshop_transaction_contents.transaction_id= webshop_transactions.id
            WHERE webshop_transaction_actions.status='pending' AND webshop_transactions.status='completed'
            """)

        return [
            {
                "item": {
                    "id": v[0],
                    "transaction_id": v[1],
                    "product_id": v[2],
                    "count": v[3],
                    "amount": str(v[4]),
                },
                "action": {
                    "id": v[6],
                    "name": v[7],
                },
                "pending_action": {
                    "id": v[9],
                    "value": v[5],
                },
                "member_id": v[8],
            } for v in cur.fetchall()
        ]


# TODO: More restrictive permissions?
@instance.route("transaction/<int:id>/content", methods=["GET"], permission="webshop")
@route_helper
def transaction_contents(id: int) -> Dict[str,Any]:
    '''
    Return all content related to a transaction
    '''

    with db.cursor() as cur:
        cur.execute("""
            SELECT webshop_transaction_contents.id AS content_id, webshop_products.name AS product_name,
                   webshop_products.id AS product_id, webshop_transaction_contents.count, webshop_transaction_contents.amount
            FROM webshop_transaction_contents
            INNER JOIN webshop_products ON webshop_products.id = webshop_transaction_contents.product_id
            WHERE  webshop_transaction_contents.transaction_id = %s
            """, id)
        return [
            {
                "content_id": v[0],
                "product_name": v[1],
                "product_id": v[2],
                "count": v[3],
                "amount": str(v[4]),
            } for v in cur.fetchall()
        ]

@instance.route("transaction/<int:id>/actions", methods=["GET"], permission="webshop")
@route_helper
def transaction_actions(id: int):
    '''
    Return all actions related to a transaction
    '''

    with db.cursor() as cur:
        cur.execute("""
            SELECT webshop_actions.id AS action_id, webshop_actions.name AS action, 
                    webshop_transaction_contents.id AS content_id, webshop_transaction_actions.value, webshop_transaction_actions.status, webshop_transaction_actions.completed_at
            FROM webshop_transaction_contents
            INNER JOIN webshop_transaction_actions ON webshop_transaction_actions.content_id = webshop_transaction_contents.id
            INNER JOIN webshop_actions ON webshop_actions.id = webshop_transaction_actions.action_id
            WHERE webshop_transaction_contents.transaction_id = %s
            """, id)
        return [
            {
                "action_id": v[0],
                "action": v[1],
                "content_id": v[2],
                "value": v[3],
                "status": v[4],
                "completed_at": format_datetime(v[5]),
            } for v in cur.fetchall()
        ]

@instance.route("transaction/<int:id>/events", methods=["GET"], permission="webshop")
@route_helper
def transaction_events(id: int):
    return transaction_content_entity.list("transaction_id=%s", id)

@instance.route("transactions_extended_info", methods=["GET"], permission="webshop")
@route_helper
def list_orders():
    transactions = transaction_entity.list()
    member_ids = ",".join(set([str(t["member_id"]) for t in transactions]))

    r = instance.gateway.get(f"membership/member?member_id={member_ids}")
    assert(r.ok)

    member_data = {d["member_id"]: d for d in r.json()["data"]}
    for t in transactions:
        member = member_data[t["member_id"]]
        t["member_name"] = f"{member['firstname']} {member['lastname']}"
        t["member_number"] = member['member_number']

    return transactions

@instance.route("member/current/transactions", methods=["GET"], permission=None)
@route_helper
def member_history() -> Dict[str,Any]:
    '''
    Helper for listing the full transaction history of a member, with product info included.
    '''
    user_id = assert_get(request.headers, "X-User-Id")

    # TODO: All these database lookups could probably be optimized
    transactions = transaction_entity.list("member_id=%s", user_id)
    transactions.reverse()
    for tr in transactions:
        items = transaction_content_entity.list("transaction_id=%s", tr["id"])
        for item in items:
            item["product"] = product_entity.get(item["product_id"])

        tr["content"] = items

    return transactions


def copy_dict(source: Dict[str,Any], fields: List[str]) -> Dict[str,Any]:
    return {key: source[key] for key in fields if key in source}


def send_new_member_email(member_id: int) -> None:
    r = instance.gateway.post("messages", {
        "recipients": [
            {
                "type": "member",
                "id": member_id
            },
        ],
        "message_type": "email",
        "subject": "Välkommen till Stockholm Makerspace",
        "subject_en": "Welcome to the Stockholm Makerspace",
        "body": render_template("new_member_email.html", frontend_url=instance.gateway.get_frontend_url)
    })

    if not r.ok:
        eprint("Failed to send new member email")
        eprint(r.text)


@instance.route("register", methods=["POST"], permission=None)
@route_helper
def register() -> Dict[str, int]:
    ''' Register a new member.
        See frontend.py:register_member
    '''

    data = request.get_json()
    if data is None:
        raise MissingJson()

    products = membership_products(db)

    purchase = assert_get(data, "purchase")
    if len(purchase["cart"]) != 1:
        raise CartMustContainNItems(1)
    item = purchase["cart"][0]
    if item["count"] != 1:
        raise CartMustContainNItems(1)
    if item["id"] not in (p["id"] for p in products):
        raise NotAllowedToPurchase(item['id'])

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
        # Ideally should just return r.text, but the helper code for routes screws that up a bit right now.
        # This may happen when for example a user with the same email exists.
        abort(r.status_code, r.json()["message"])

    member = r.json()["data"]
    member_id = member["member_id"]

    # Delete the member immediately, this is because the member is not yet activated because
    # the payment has not yet been done. The member will be un-deleted when the payment goes through.
    r = instance.gateway.delete(f"membership/member/{member_id}")
    assert(r.ok)

    # Construct the purchase object again, using user data is always risky
    purchase = {
        "cart": [
            {
                "id": item["id"],
                "count": 1
            }
        ],
        "expectedSum": purchase["expectedSum"],
        "stripeSource": purchase["stripeSource"],
        "duplicatePurchaseRand": purchase["duplicatePurchaseRand"],
    }

    # Note this will throw if the payment fails
    return pay(member_id=member_id, data=purchase, activates_member=True)


@instance.route("stripe_callback", methods=["POST"], permission=None)
@route_helper
def stripe_callback() -> None:
    payload = request.data
    eprint("Headers: " + str(request.headers))
    sig_header = request.headers['Stripe-Signature']
    event = None

    try:
        event = stripe.Webhook.construct_event(
          payload, sig_header, stripe_signing_secret
        )
    except ValueError as e:
        # Invalid payload
        abort(400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        abort(400)

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


def process_cart(cart: List[Dict[str,Any]]) -> Tuple[Decimal, List[CartItem]]:
    with db.cursor() as cur:
        prices = []
        multiples = []
        for item in cart:
            cur.execute("SELECT price,smallest_multiple FROM webshop_products WHERE id=%s AND deleted_at IS NULL", item["id"])
            tup: Tuple[Decimal, int] = cur.fetchone()
            if tup is None:
                raise NoSuchItem(str(item["id"]))
            price, smallest_multiple = tup
            if price < 0:
                abort(400, "Item seems to have a negatice price. Not allowing purchases that item just in case. Item: " + str(item["id"]))
            prices.append(price)
            multiples.append(smallest_multiple)

        items = []
        with localcontext() as ctx:
            ctx.clear_flags()
            total_amount = Decimal(0)

            for price, smallest_multiple, item in zip(prices, multiples, cart):
                count = int(item["count"])
                if count <= 0:
                    raise NonNegativeItemCount(str(item["id"]))
                if (count % smallest_multiple) != 0:
                    raise InvalidItemCountMultiple(str(item["id"]), smallest_multiple, count)

                item_amount = price * count
                items.append(CartItem(item["id"], count, item_amount))
                total_amount += item_amount

            if ctx.flags[Rounded]:
                # This can possibly happen with huge values, I suppose they will be caught below anyway but it's good to catch in any case
                raise RoundingError()

    return total_amount, items


def validate_payment(cart: List[Dict[str,Any]], expected_amount: Decimal) -> Tuple[Decimal, List[CartItem]]:
    if len(cart) == 0:
        raise EmptyCart()

    total_amount, items = process_cart(cart)

    # Ensure that the frontend hasn't calculated the amount to pay incorrectly
    if abs(total_amount - Decimal(expected_amount)) > Decimal("0.01"):
        return NonMatchingSums(expected_amount, total_amount)

    if total_amount > 10000:
        raise TooLargeAmount(10000)

    # Assert that the amount can be converted to a valid stripe amount
    convert_to_stripe_amount(total_amount)

    return total_amount, items


def convert_to_stripe_amount(amount: Decimal) -> int:
    # Ensure that the amount to pay is in whole cents (ören)
    # This shouldn't be able to fail as all products in the database have prices in cents, but you never know.
    stripe_amount = amount * stripe_currency_base
    if (stripe_amount % 1) != 0:
        raise NotPurelyCents(amount)

    # The amount is stored as a Decimal, convert it to an int
    return int(stripe_amount)


def stripe_payment(transaction_id: int, token: str) -> None:
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
    except stripe.CardError as e:
        body = e.json_body
        err = body.get('error', {})
        eprint("Stripe Charge Failed\n" + str(err))
        raise PaymentFailed(err.get("message"))
    except stripe.StripeError as e:
        eprint("Stripe Charge Failed\n" + str(e))
        raise PaymentFailed()
    except Exception as e:
        eprint("Stripe Charge Failed")
        eprint(e)
        raise PaymentFailed()

    transaction["status"] = "completed"
    transaction_entity.put(transaction, transaction_id)

    # Check if this transaction is a new member registration
    if webshop_pending_registrations.list("transaction_id=%s", [transaction_id]):
        activate_member(transaction["member_id"])

    send_receipt_email(transaction["member_id"], transaction_id)
    eprint("Payment complete. id: " + str(transaction_id))


def activate_member(member_id: int) -> None:
    # Make the member not be deleted
    r = instance.gateway.post(f"membership/member/{member_id}/activate", {})
    assert r.ok

    send_new_member_email(member_id)


def send_receipt_email(member_id: int, transaction_id: int) -> None:
    transaction = transaction_entity.get(transaction_id)
    items = transaction_content_entity.list("transaction_id=%s", transaction_id)
    products = [product_entity.get(item["product_id"]) for item in items]

    r = instance.gateway.get(f"membership/member/{member_id}")
    assert r.ok

    member = r.json()["data"]

    r = instance.gateway.post("messages", {
        "recipients": [
            {
                "type": "member",
                "id": member_id
            },
        ],
        "message_type": "email",
        "subject": "Kvitto - Stockholm Makerspace",
        "subject_en": "Receipt - Stockholm Makerspace",
        "body": render_template("receipt_email.html", cart=zip(products,items), transaction=transaction, currency="kr", member=member, frontend_url=instance.gateway.get_frontend_url)
    })

    if not r.ok:
        eprint("Failed to send receipt email")
        eprint(r.text)


duplicatePurchaseRands: Set[int] = set()


@instance.route("pay", methods=["POST"], permission=None)
@route_helper
def pay_route() -> Dict[str,int]:
    data = request.get_json()
    if data is None:
        raise MissingJson()

    member_id = int(assert_get(request.headers, "X-User-Id"))
    return pay(member_id, data)


def add_transaction_to_db(member_id: int, total_amount: Decimal, items: List[CartItem]) -> int:
    transaction_id = transaction_entity.post({"member_id": member_id, "amount": total_amount, "status": "pending"})["id"]
    for item in items:
        item_content = transaction_content_entity.post({"transaction_id": transaction_id, "product_id": item.id, "count": item.count, "amount": item.amount})
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO webshop_transaction_actions (content_id, action_id, value, status)
                SELECT %s AS content_id, action_id, SUM(%s * value) AS value, 'pending' AS status 
                FROM webshop_product_actions 
                WHERE product_id=%s AND deleted_at IS NULL
                GROUP BY action_id
                """, (item_content["id"], item.count, item.id))

    return transaction_id


def create_stripe_source(transaction_id: int, card_source: str, total_amount: Decimal) -> stripe.Source:
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


def pay(member_id: int, data: Dict[str, Any], activates_member: bool = False) -> Dict[str, int]:
    # The frontend will add a per-page random value to the request.
    # This will try to prevent duplicate payments due to sending the payment request twice
    duplicatePurchaseRand = assert_get(data, "duplicatePurchaseRand")
    if duplicatePurchaseRand in duplicatePurchaseRands:
        raise DuplicateTransaction()

    if member_id <= 0:
        raise NotMember()

    total_amount, items = validate_payment(data["cart"], data["expectedSum"])

    transaction_id = add_transaction_to_db(member_id, total_amount, items)

    if activates_member:
        # Mark this transaction as one that is for registering a member
        webshop_pending_registrations.post({"transaction_id": transaction_id})

    card_source = assert_get(data, "stripeSource")

    try:
        source = create_stripe_source(transaction_id, card_source, total_amount)
    except stripe.error.InvalidRequestError as e:
        if "Amount must convert to at least" in str(e):
            return TooSmallAmount()
        else:
            eprint("Stripe Charge Failed")
            eprint(e)
            abort(400, "payment failed")

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
