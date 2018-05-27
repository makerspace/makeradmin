from flask import Flask, render_template
import service
from service import eprint
import json
from webshop_entities import category_entity, product_entity, transaction_entity, transaction_content_entity

instance = service.create_frontend(url="shop", port=80)

# Grab the database so that we can use it inside requests
db = instance.db

product_entity.db = db
category_entity.db = db
transaction_entity.db = db
transaction_content_entity.db = db


@instance.route("/")
def home():
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

    product_json = json.dumps(data)
    return render_template("shop.html", product_json=product_json, categories=categories, url=instance.full_path)


@instance.route("product/<int:id>/edit")
def product_edit(id):
    categories = category_entity.list()
    product = product_entity.get(id)
    return render_template("product_edit.html", product=product, categories=categories, url=instance.full_path)


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
    }

    return render_template("product_edit.html", product=product, categories=categories, url=instance.full_path)


@instance.route("receipt/<int:id>")
def receipt(id):
    transaction = transaction_entity.get(id)
    items = transaction_content_entity.list("transaction_id=%s", id)
    products = [product_entity.get(item["id"]) for item in items]

    return render_template("receipt.html", cart=zip(products,items), transaction=transaction, currency="kr", url=instance.full_path)


instance.serve_indefinitely()
