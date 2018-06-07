from flask import Flask, render_template, abort
import service
from service import eprint
import json
import os
from webshop_entities import category_entity, product_entity, transaction_entity, transaction_content_entity, action_entity, membership_products

instance = service.create_frontend(url="shop", port=80)

# Grab the database so that we can use it inside requests
db = instance.db

product_entity.db = db
category_entity.db = db
transaction_entity.db = db
transaction_content_entity.db = db
action_entity.db = db

host_backend = os.environ["HOST_BACKEND"]
if not host_backend.startswith("http"):
    host_backend = "https://" + host_backend

meta = {
    "apiBasePath": host_backend,
    "stripePublicKey": os.environ["STRIPE_PUBLIC_KEY"]
}

def product_data():
    with db.cursor() as cur:
        # Get all categories, as some products may exist in deleted categories
        # (it is up to an admin to move them to another category)
        categories = category_entity.list(where=None)

        data = []
        for cat in categories:
            cur.execute("SELECT id,name,unit,price,smallest_multiple FROM webshop_products WHERE category_id=%s AND deleted_at IS NULL ORDER BY name", (cat["id"],))
            products = cur.fetchall()
            if len(products) > 0:
                data.append({
                    "id": cat["id"],
                    "name": cat["name"],
                    "items": [
                        {
                            "id": item[0],
                            "name": item[1],
                            "unit": item[2],
                            "price": str(item[3]),
                            "smallest_multiple": str(item[4]),
                        } for item in products
                    ]
                })

        # Only show existing columns in the sidebar
        categories = category_entity.list()
        return data, categories


@instance.route("/")
def home():
    all_products, categories = product_data()
    return render_template("shop.html", product_json=json.dumps(all_products), categories=categories, url=instance.full_path, meta=meta)


@instance.route("register")
def register_member():
    products = membership_products(db)
    all_products, _ = product_data()
    return render_template("register.html", product_json=json.dumps(all_products), products=products, currency="kr", url=instance.full_path, meta=meta)


@instance.route("member/<int:id>/history")
def purchase_history(id):
    # TODO: All these database lookups could probably be optimized
    r = instance.gateway.get(f"membership/member/{id}")
    if r.status_code == 404:
        return render_template("member_404.html", url=instance.full_path), r.status_code
    elif not r.ok:
        abort(r.status_code, r.json()["message"])

    member = r.json()["data"]
    return render_template("history.html", member=member, url=instance.full_path, meta=meta)


@instance.route("product/<int:id>/edit")
def product_edit(id):
    categories = category_entity.list()
    product = product_entity.get(id)

    # Find the ids and names of all actions that this product has
    with db.cursor() as cur:
        cur.execute("SELECT webshop_product_actions.id,webshop_actions.id,webshop_actions.name,webshop_product_actions.value FROM webshop_product_actions INNER JOIN webshop_actions ON webshop_product_actions.action_id=webshop_actions.id WHERE webshop_product_actions.product_id=%s AND webshop_product_actions.deleted_at IS NULL", id)
        actions = cur.fetchall()
        eprint(actions)
        actions = [{
            "id": a[0],
            "action_id": a[1],
            "name": a[2],
            "value": a[3],
        } for a in actions]

    action_categories = action_entity.list()
    action_json = json.dumps({
        "actions": actions,
        "action_categories": action_categories
    })

    return render_template("product_edit.html", action_json=action_json, action_categories=action_categories, product=product, categories=categories, url=instance.full_path, meta=meta)


@instance.route("product/create")
def product_create():
    categories = category_entity.list()

    product = {
        "category_id": "",
        "name": "",
        "description": "",
        "unit": "",
        "price": 0.0,
        "id": "new",
        "smallest_multiple": 1,
    }

    action_categories = action_entity.list()
    action_json = json.dumps({
        "actions": [],
        "action_categories": action_categories
    })

    return render_template("product_edit.html", action_json=action_json, action_categories=action_categories, product=product, categories=categories, url=instance.full_path, meta=meta)


@instance.route("receipt/<int:id>")
def receipt(id):
    transaction = transaction_entity.get(id)
    items = transaction_content_entity.list("transaction_id=%s", id)
    products = [product_entity.get(item["product_id"]) for item in items]

    return render_template("receipt.html", cart=zip(products,items), transaction=transaction, currency="kr", url=instance.full_path, meta=meta)


instance.serve_indefinitely()
