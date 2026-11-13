from flask import Blueprint, redirect, render_template, url_for

from database.connection import db
from routes.auth import current_customer

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.get("/")
def list_orders():
    customer = current_customer()
    if customer is None:
        return redirect(url_for("auth.login"))

    orders = db.hoadon.find({"customer_id": customer["_id"]}).sort([("created_at", -1), ("_id", -1)])
    return render_template("orders.html", orders=list(orders))
