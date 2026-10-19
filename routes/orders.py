from flask import Blueprint, render_template

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.get("/")
def list_orders():
    return render_template("placeholder.html", title="Đơn hàng", message="Danh sách đơn hàng sẽ được triển khai tiếp.")
