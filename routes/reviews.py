from datetime import datetime, timezone
from hmac import compare_digest

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from database.connection import db
from routes.auth import current_customer
from routes.products import find_product

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.get("/")
def reviews_home():
    return render_template("placeholder.html", title="Đánh giá sản phẩm", message="Chức năng đánh giá sẽ được triển khai tiếp.")


@reviews_bp.post("/products/<product_id>")
def add_review(product_id):
    customer = current_customer()
    if customer is None:
        return redirect(url_for("auth.login"))

    token = session.get("review_csrf")
    if not token or not compare_digest(token.encode(), request.form.get("csrf_token", "").encode()):
        abort(400)

    product = find_product(db.sanpham, product_id)
    rating = request.form.get("rating", type=int)
    content = request.form.get("content", "").strip()
    if rating not in range(1, 6) or not 1 <= len(content) <= 2000:
        flash("Chọn từ 1 đến 5 sao và nhập nhận xét tối đa 2.000 ký tự.", "review_error")
    else:
        db.reviews.insert_one({
            "product_id": product["_id"],
            "user_id": customer["_id"],
            "customer_name": customer.get("name") or "Khách hàng",
            "rating": rating,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        })
        flash("Đã gửi đánh giá.", "review_success")

    return redirect(url_for("products.product_detail", product_id=product["_id"], _anchor="reviews"))
