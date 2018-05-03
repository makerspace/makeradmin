from flask import Flask, request, abort, jsonify, render_template
import service
from service import eprint, assert_get

with service.create_frontend(url="shop", port=80) as instance:
    app = Flask(__name__, static_url_path=instance.full_path("static"))

    # Grab the database so that we can use it inside requests
    db = instance.db

    @app.route(instance.full_path(""))
    def home():
        # with db.cursor() as cur:
        #     cur.execute("SELECT member_id FROM webshop_products WHERE email=%s", (user_tag,))
        # user_id = assert_get(request.headers, "X-User-Id")
        return render_template("shop.html", url=instance.full_path)

    instance.serve_indefinitely(app)
