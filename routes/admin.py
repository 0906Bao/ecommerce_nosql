from datetime import date, datetime, time, timedelta, timezone
from math import isfinite

from flask import Blueprint, abort, render_template, request, redirect, url_for
from routes.categories import category_names
from database.connection import db
from routes.products import find_product
from routes.auth import admin_required  # Import decorator phân quyền

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/', endpoint='dashboard_root')
@admin_bp.route('/admin', endpoint='dashboard_root_short')
@admin_required
def admin_dashboard_root():
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/dashboard', endpoint='dashboard')
@admin_required
def admin_dashboard():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    period = request.args.get('period', 'day')
    formats = {'day': '%Y-%m-%d', 'month': '%Y-%m'}
    if period not in formats:
        abort(400, 'Invalid reporting period')

    local_timezone = timezone(timedelta(hours=7))
    bounds = {}
    try:
        if start:
            bounds['$gte'] = datetime.combine(date.fromisoformat(start), time.min, local_timezone)
        if end:
            bounds['$lt'] = datetime.combine(date.fromisoformat(end) + timedelta(days=1), time.min, local_timezone)
    except (ValueError, OverflowError):
        abort(400, 'Invalid report date')
    if start and end and bounds['$gte'] >= bounds['$lt']:
        abort(400, 'Invalid report date range')

    filters = {'created_at': bounds} if bounds else {'created_at': {'$type': 'date'}}
    match = {'$match': filters}
    total_orders = db.hoadon.count_documents(filters)
    total_products = db.sanpham.count_documents({})

    revenue_by_period = list(db.hoadon.aggregate([
        match,
        {'$group': {
            '_id': {'$dateToString': {'format': formats[period], 'date': '$created_at', 'timezone': '+07:00'}},
            'total_revenue': {'$sum': '$total_amount'},
            'orders': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}},
    ]))
    total_revenue = sum(row['total_revenue'] for row in revenue_by_period)

    top_products = list(db.hoadon.aggregate([
        match,
        {'$sort': {'created_at': -1, '_id': -1}},
        {'$unwind': '$items'},
        {'$group': {
            '_id': {'$toString': '$items.product_id'},
            'name': {'$first': '$items.name'},
            'total_sold': {'$sum': '$items.quantity'},
            'total_revenue': {'$sum': '$items.subtotal'}
        }},
        {'$sort': {'total_sold': -1, '_id': 1}},
        {'$limit': 5},
    ]))

    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        total_products=total_products,
        total_revenue=total_revenue,
        revenue_by_period=revenue_by_period,
        start=start, end=end, period=period,
        top_products=top_products
    )


@admin_bp.route('/admin/products', endpoint='manage_products')
@admin_required
def manage_products():
    products = list(db.sanpham.find({}).sort('name', 1))
    return render_template('admin/manage_products.html', products=products)


@admin_bp.route('/admin/products/add', methods=['GET', 'POST'], endpoint='add_product')
@admin_required
def add_product():
    return product_form()


@admin_bp.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    return product_form(find_product(db.sanpham, product_id))


def product_form(existing=None):
    product = existing or {}
    categories = category_names()
    if request.method == 'GET':
        return render_template('admin/add_product.html', product=product, categories=categories, editing=existing is not None)

    product = {field: request.form.get(field, '').strip()
               for field in ('name', 'category', 'price', 'stock', 'description', 'image')}
    attributes = dict((existing or {}).get('attributes') or {})
    for field in ('cpu', 'ram', 'material', 'power', 'origin'):
        value = request.form.get(field, '').strip()
        if value:
            attributes[field] = value
        else:
            attributes.pop(field, None)
    sizes = [size.strip() for size in request.form.get('size', '').split(',') if size.strip()]
    if sizes:
        attributes['size'] = sizes
    else:
        attributes.pop('size', None)
    product['attributes'] = attributes

    try:
        price = float(product['price'])
        stock = int(product['stock'])
        if not product['name'] or product['category'] not in categories or not isfinite(price) or price < 0 or not 0 <= stock < 2**63:
            raise ValueError
    except ValueError:
        return render_template('admin/add_product.html', product=product, categories=categories,
                               editing=existing is not None, error=True), 400

    product.update(price=price, stock=stock)
    if existing is None:
        db.sanpham.insert_one(product)
    else:
        result = db.sanpham.update_one({'_id': existing['_id']}, {'$set': product})
        if not result.matched_count:
            abort(404)
    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/admin/products/delete/<product_id>', methods=['POST'], endpoint='delete_product')
@admin_required
def delete_product(product_id):
    product = find_product(db.sanpham, product_id)
    db.sanpham.delete_one({'_id': product['_id']})
    return redirect(url_for('admin.manage_products'))
