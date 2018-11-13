from flask import render_template
import service
import json
from webshop_entities import category_entity, product_entity, transaction_entity, transaction_content_entity, \
    action_entity, product_image_entity


instance = service.create_frontend("shop", url="shop", port=None)

# Grab the database so that we can use it inside requests
db = instance.db

product_entity.db = db
category_entity.db = db
transaction_entity.db = db
transaction_content_entity.db = db
action_entity.db = db
product_image_entity.db = db


@instance.route("/")
def home() -> str:
    return render_template("shop.html")


@instance.route("cart")
def cart() -> str:
    return render_template("cart.html")


@instance.route("register")
def register_member() -> str:
    return render_template("register.html")


@instance.route("member/history")
def purchase_history() -> str:
    return render_template("history.html")


@instance.route("product/<product_id>")
def product_view(product_id: int) -> str:
    return render_template("product.html", product_id=product_id)


@instance.route("product/<int:product_id>/edit")
def product_edit(product_id: int) -> str:
    return render_template("product_edit.html", product_id=product_id)


@instance.route("product/create")
def product_create() -> str:
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

    return render_template("product_edit.html", action_json=action_json, action_categories=action_categories, product=product, categories=categories)


@instance.route("receipt/<int:transaction_id>")
def receipt(transaction_id: int) -> str:
    return render_template("receipt.html", transaction_id=transaction_id)


@instance.route("statistics")
def statistics() -> str:
    return render_template("statistics.html")


instance.serve_indefinitely()
