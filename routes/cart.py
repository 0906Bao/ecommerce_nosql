from flask import Blueprint, render_template

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.get("/")
def view_cart():
    return render_template("placeholder.html", title="Giỏ hàng", message="Giỏ hàng sẽ được triển khai tiếp.")
