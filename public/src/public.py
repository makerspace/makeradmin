import os
import sys
from logging import INFO, basicConfig, getLogger
from typing import Any

import flask
from flask import Blueprint, Flask, redirect, send_from_directory, url_for
from flask_babel import Babel

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


class Section(Blueprint):
    def __init__(self, name):
        super().__init__(name, name)
        self.context_processor(lambda: dict(url=self.url))

    def url(self, path):
        return f"/{self.name}{path}"

    def route(self, path, **kwargs):
        return super().route(self.url(path), **kwargs)


def get_locale():
    # # if a user is logged in, use the locale from the user settings
    # user = getattr(g, 'user', None)
    # if user is not None:
    #     return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return flask.request.accept_languages.best_match(["en", "sv"])


def render_template(path: str, **kwargs: Any) -> str:
    return flask.render_template(path, banner=banner, sidebar_additional_classes=sidebar_additional_classes, **kwargs)


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


@shop.route("/register2")
def register_member2() -> str:
    return render_template("register2.html")


@shop.route("/member/history")
def purchase_history():
    return render_template("history.html")


@shop.route("/member/courses")
def courses():
    return render_template("courses.html")


@shop.route("/member/licenses")
def licenses():
    return render_template("licenses.html")


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


@member.route("/change_phone")
def change_phone():
    return render_template("change_phone.html")


@member.route("/reset_password")
def reset_password():
    return render_template("reset_password.html")


static_hash = os.environ["STATIC_PREFIX_HASH"]
app = Flask(__name__, static_url_path=f"/static{static_hash}", static_folder="../static")
babel = Babel(app, locale_selector=get_locale)
sys.stderr.write("STATIC URL PATH" + app.static_url_path + "\n")
app.register_blueprint(shop)
app.register_blueprint(member)


@app.route("/static/product_images/<path:path>")
def product_image(path):
    return send_from_directory("../static/product_images", path)


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
            api_base_url=api_base_url, stripe_public_key=os.environ["STRIPE_PUBLIC_KEY"], host_public=host_public
        ),
    )
