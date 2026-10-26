from flask import Blueprint, render_template, request, redirect, url_for
from database.connection import db
from bson.objectid import ObjectId
from routes.auth import admin_required  # Import decorator phân quyền

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard', endpoint='dashboard')
@admin_required
def admin_dashboard():
    total_orders = db.hoadon.count_documents({})
    total_products = db.sanpham.count_documents({})

    revenue_pipeline = [
        {"$group": {"_id": None, "total_revenue": {"$sum": "$total_amount"}}}
    ]
    revenue_result = list(db.hoadon.aggregate(revenue_pipeline))
    total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0

    top_products_pipeline = [
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.name",
            "total_sold": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": "$items.subtotal"}
        }},
        {"$sort": {"total_sold": -1}},
        {"$limit": 5}
    ]
    top_products = list(db.hoadon.aggregate(top_products_pipeline))

    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        total_products=total_products,
        total_revenue=total_revenue,
        top_products=top_products
    )

@admin_bp.route('/admin/products', endpoint='manage_products')
@admin_required
def manage_products():
    products = list(db.sanpham.find({}))
    return render_template('admin/manage_products.html', products=products)

@admin_bp.route('/admin/products/add', methods=['GET', 'POST'], endpoint='add_product')
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        description = request.form.get('description', '')

        attributes = {}
        if category == 'Điện tử':
            attributes['cpu'] = request.form.get('cpu', '')
            attributes['ram'] = request.form.get('ram', '')
        elif category == 'Thời trang':
            size_raw = request.form.get('size', '')
            attributes['size'] = [s.strip() for s in size_raw.split(',')]
            attributes['material'] = request.form.get('material', '')
        elif category == 'Gia dụng':
            attributes['power'] = request.form.get('power', '')
            attributes['origin'] = request.form.get('origin', '')

        new_product = {
            'name': name,
            'category': category,
            'price': price,
            'stock': stock,
            'description': description,
            'attributes': attributes
        }

        db.sanpham.insert_one(new_product)
        return redirect(url_for('admin.manage_products'))

    return render_template('admin/add_product.html')

@admin_bp.route('/admin/products/delete/<product_id>', methods=['POST'], endpoint='delete_product')
@admin_required
def delete_product(product_id):
    try:
        db.sanpham.delete_one({'_id': ObjectId(product_id)})
    except Exception:
        db.sanpham.delete_one({'_id': product_id})
    return redirect(url_for('admin.manage_products'))