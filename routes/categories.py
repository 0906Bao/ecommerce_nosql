from flask import Blueprint, jsonify
from database.connection import get_db

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


@categories_bp.get("/api")
def list_categories():
    categories = list(get_db().sanpham.distinct("category"))
    if not categories:
        categories = list(get_db().danhmuc.find({}, {"ten": 1, "mo_ta": 1}).limit(100))
        for category in categories:
            category["id"] = str(category.pop("_id"))
            category["name"] = category.get("ten") or category.get("name")
            category.pop("ten", None)
        return jsonify(categories)

    payload = [{"id": category, "name": category} for category in categories]
    return jsonify(payload)
