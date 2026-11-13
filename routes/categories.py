from bson import ObjectId
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from pymongo.errors import DuplicateKeyError

from database.connection import get_db
from routes.auth import admin_required

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


def categories():
    db = get_db()
    result = {}
    for row in db.danhmuc.find({}):
        name = row.get("ten") or row.get("name")
        if name:
            result[name] = {"id": str(row["_id"]), "name": name, "mo_ta": row.get("mo_ta", ""), "managed": True}
    for name in db.sanpham.distinct("category"):
        if isinstance(name, str) and name:
            result.setdefault(name, {"id": name, "name": name, "managed": False})
    return sorted(result.values(), key=lambda row: row["name"].casefold())


def category_names():
    return [row["name"] for row in categories()]


@categories_bp.get("/api")
def list_categories():
    return jsonify(categories())


@categories_bp.route("/manage", methods=["GET", "POST"])
@admin_required
def manage_categories():
    if request.method == "POST":
        save_category()
        return redirect(url_for("categories.manage_categories"))
    return render_template("admin/manage_categories.html", categories=categories())


def find_category(category_id):
    if not ObjectId.is_valid(category_id):
        abort(404)
    row = get_db().danhmuc.find_one({"_id": ObjectId(category_id)})
    if row is None:
        abort(404)
    return row


def save_category(existing=None):
    db = get_db()
    name = request.form.get("name", "").strip()
    if not name:
        abort(400, "Vui lòng nhập tên danh mục.")
    old_name = (existing.get("ten") or existing.get("name")) if existing else None
    if existing and name != old_name and db.sanpham.find_one({"category": old_name}):
        abort(409, "Chuyển sản phẩm sang danh mục khác trước khi đổi tên.")
    duplicate = db.danhmuc.find_one({"$or": [{"ten": name}, {"name": name}]})
    if duplicate and (existing is None or duplicate["_id"] != existing["_id"]):
        abort(409, "Tên danh mục đã tồn tại.")
    values = {"ten": name, "mo_ta": request.form.get("description", "").strip()}
    try:
        if existing:
            result = db.danhmuc.update_one({"_id": existing["_id"]}, {"$set": values, "$unset": {"name": ""}})
            if not result.matched_count:
                abort(404)
        else:
            db.danhmuc.insert_one(values)
    except DuplicateKeyError:
        abort(409, "Tên danh mục đã tồn tại.")


@categories_bp.post("/manage/<category_id>/edit")
@admin_required
def edit_category(category_id):
    save_category(find_category(category_id))
    return redirect(url_for("categories.manage_categories"))


@categories_bp.post("/manage/<category_id>/delete")
@admin_required
def delete_category(category_id):
    db = get_db()
    row = find_category(category_id)
    if db.sanpham.find_one({"category": row.get("ten") or row.get("name")}):
        abort(409, "Chuyển sản phẩm sang danh mục khác trước khi xóa.")
    db.danhmuc.delete_one({"_id": row["_id"]})
    return redirect(url_for("categories.manage_categories"))
