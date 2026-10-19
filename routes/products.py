from flask import Blueprint, render_template, request
from database.connection import get_db

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.get("/")
def list_products():
    # Bộ lọc sẽ được bổ sung trong giai đoạn CRUD.
    db = get_db()
    products = list(db.sanpham.find({"trang_thai": {"$ne": "ngung_ban"}}).limit(50))
    for product in products:
        product["id"] = str(product.pop("_id"))
    return render_template("products.html", title="Sản phẩm", products=products)
