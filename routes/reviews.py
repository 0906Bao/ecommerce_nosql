from flask import Blueprint, render_template

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.get("/")
def reviews_home():
    return render_template("placeholder.html", title="Đánh giá sản phẩm", message="Chức năng đánh giá sẽ được triển khai tiếp.")
