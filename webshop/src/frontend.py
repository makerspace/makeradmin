from flask import render_template
import service


instance = service.create_frontend("shop", url="shop", port=None)


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
    return render_template("product_edit.html", product_id=0)


@instance.route("receipt/<int:transaction_id>")
def receipt(transaction_id: int) -> str:
    return render_template("receipt.html", transaction_id=transaction_id)


@instance.route("statistics")
def statistics() -> str:
    return render_template("statistics.html")


instance.serve_indefinitely()
