from flask import Flask, render_template
import service
from service import eprint
import json
from backend import product_entity
from backend import category_entity

with service.create_frontend(url="shop", port=80) as instance:
    app = Flask(__name__, static_url_path=instance.full_path("static"))

    # Grab the database so that we can use it inside requests
    db = instance.db

    product_entity.db = db
    category_entity.db = db

    @app.route(instance.full_path(""))
    def home():
        with db.cursor() as cur:
            # Get all categories, as some products may exist in deleted categories
            # (it is up to an admin to move them to another category)
            categories = category_entity.list(where=None)

            data = []
            for cat in categories:
                cur.execute("SELECT id,name,unit,price FROM webshop_products WHERE category_id=%s AND deleted_at IS NULL ORDER BY name", (cat["id"],))
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
                            } for item in products
                        ]
                    })

            # Only show existing columns in the sidebar
            categories = category_entity.list()

        product_json = json.dumps(data)
        return render_template("shop.html", product_json=product_json, categories=categories, url=instance.full_path)

    @app.route(instance.full_path("product/<int:id>/edit"))
    def product_edit(id):
        categories = category_entity.list()
        product = product_entity.get(id)
        return render_template("product_edit.html", product=product, categories=categories, url=instance.full_path)

    @app.route(instance.full_path("product/create"))
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

    instance.serve_indefinitely(app)
