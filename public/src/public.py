import os
import sys
from logging import INFO, basicConfig, getLogger
from typing import Any

import flask
from flask import Blueprint, Flask, redirect, send_from_directory, url_for

basicConfig(
    format="%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s",
    stream=sys.stderr,
    level=INFO,
)


logger = getLogger("makeradmin")

# This is the current global banner.
# Set to an empty string ("") to disable.
banner = ""

sidebar_additional_classes = ""
if banner:
    # Set the sidebar to not to use fixed positioning if there is a banner because otherwise the sidebar may end up below the banner, esp. on mobile devices
    sidebar_additional_classes = "sidebar-banner-adjust"

static_hash = os.environ["STATIC_PREFIX_HASH"]
HOST_PUBLIC = os.environ["HOST_PUBLIC"]


class Section(Blueprint):
    def __init__(self, name):
        super().__init__(name, name)
        self.context_processor(lambda: dict(url=self.url))

    def url(self, path):
        return f"/{self.name}{path}"

    def route(self, path, **kwargs):
        return super().route(self.url(path), **kwargs)


def render_template(path: str, **kwargs: Any) -> str:
    assert "STATIC" not in kwargs
    return flask.render_template(
        path,
        banner=banner,
        sidebar_additional_classes=sidebar_additional_classes,
        # Note: Using fully-qualified URL to avoid issues where HOST_PUBLIC contains a path (e.g. mytestserver.com/makerspace/)
        STATIC=f"{HOST_PUBLIC}/static{static_hash}",
        **kwargs,
    )


shop = Section("shop")


@shop.route("/")
def home() -> str:
    return render_template("shop.html")


@shop.route("/cart")
def cart() -> str:
    return render_template("cart.html")


@shop.route("/register")
def register_member():
    return render_template("register.html")


@shop.route("/member/history")
def purchase_history():
    return render_template("history.html")


# # Legacy route
# @shop.route("/member/courses")
# def courses():
#     return render_template("courses.html")

# # Legacy route
# @shop.route("/member/licenses")
# def licenses():
#     return render_template("licenses.html")


@shop.route("/product/<product_id>")
def product_view(product_id: int):
    return render_template("product.html", product_id=product_id)


@shop.route("/receipt/<int:transaction_id>")
def receipt(transaction_id: int):
    return render_template("receipt.html", transaction_id=transaction_id)


@shop.route("/statistics")
def statistics() -> str:
    return render_template("statistics.html")


member = Section("member")


@member.route("/")
def show_member():
    return render_template("member.html")


@member.route("/login/<string:token>")
def login(token):
    return render_template("login.html", token=token)


@member.route("/quiz/<int:quiz_id>")
def quiz_main(quiz_id: int):
    # Note: quiz_id is parsed client side
    return render_template("quiz/quiz.html")


@member.route("/quiz/")
def quiz_backwards_compatibility():
    return redirect(member.url("/quiz/1"))


# Legacy route
@shop.route("/member/courses")  # Legacy route
@member.route("/courses")
def courses():
    return render_template("courses.html")


@shop.route("/member/licenses")  # Legacy route
@member.route("/licenses")
def licenses():
    return render_template("licenses.html")


@member.route("/labels")
def labels():
    return render_template("labels.html")


@member.route("/change_phone")
def change_phone():
    return render_template("change_phone.html")


@member.route("/reset_password")
def reset_password():
    return render_template("reset_password.html")


label = Section("label")


@label.route("/<int:label_id>")
def label_detail(label_id: int):
    return render_template("label.html")


app = Flask(__name__, static_folder=None)


@app.route(f"/static{static_hash}/<path:filepath>")
def serve_static(filepath: str) -> flask.Response:
    response = send_from_directory("../static", filepath)

    # During development, the hash is empty to disable caching
    if static_hash != "":
        # Cache static files for some time. We use a prefix hash, so caching indefinitely is quite fine.
        response.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24 * 30}, immutable"
        response.headers["Vary"] = "Accept-Encoding"
    return response


app.register_blueprint(shop)
app.register_blueprint(member)
app.register_blueprint(label)


@app.route("/")
def root():
    return redirect(url_for("member.show_member"))


api_base_url = os.environ["HOST_BACKEND"]
if not api_base_url.startswith("http"):
    api_base_url = "https://" + api_base_url

host_public = os.environ["HOST_PUBLIC"]


@app.context_processor
def context():
    return dict(
        STATIC=app.static_url_path,
        meta=dict(
            api_base_url=api_base_url,
            stripe_public_key=os.environ.get("STRIPE_PUBLIC_KEY", ""),
            host_public=host_public,
            host_frontend=os.environ.get("HOST_FRONTEND", ""),
        ),
    )
