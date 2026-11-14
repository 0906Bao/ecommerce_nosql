from flask import Blueprint, redirect, render_template, url_for
from bson import ObjectId

from database.connection import db
from routes.auth import current_customer

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


def has_purchased_product(customer_id, product_id):
    # Checkout stores product IDs as strings. Older orders may contain ObjectIds.
    product_ids = [product_id, str(product_id)]
    if isinstance(product_id, str) and ObjectId.is_valid(product_id):
        product_ids.append(ObjectId(product_id))
    return db.hoadon.find_one({
        "customer_id": customer_id,
        "items": {"$elemMatch": {
            "product_id": {"$in": product_ids},
            "quantity": {"$gt": 0},
        }},
    }, {"_id": 1}) is not None


@orders_bp.get("/")
def list_orders():
    customer = current_customer()
    if customer is None:
        return redirect(url_for("auth.login"))

    orders = db.hoadon.find({"customer_id": customer["_id"]}).sort([("created_at", -1), ("_id", -1)])
    return render_template("orders.html", orders=list(orders))
