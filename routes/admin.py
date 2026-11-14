from datetime import date, datetime, time, timedelta, timezone
from math import isfinite
from io import BytesIO

from flask import Blueprint, abort, render_template, request, redirect, url_for
from PIL import Image
from routes.categories import category_names
from database.connection import db
from product_types import FIELDS, infer_product_type, product_type_options
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
    product = dict(existing or {})
    categories = category_names()
    type_options = {category: product_type_options(category) for category in categories}
    editing = existing is not None

    def render_form(**errors):
        field_values = {key: value for key, value in (product.get('attributes') or {}).items() if key in FIELDS}
        return render_template('admin/add_product.html', product=product, categories=categories,
                               editing=editing, type_options=type_options, field_labels=FIELDS,
                               field_values=field_values, **errors)

    if request.method == 'GET':
        if editing and not product.get('product_type'):
            product['product_type'] = infer_product_type(product)
        return render_form()

    product = {field: request.form.get(field, '').strip()
               for field in ('name', 'category', 'product_type', 'price', 'stock', 'description')}
    allowed_types = type_options.get(product['category'], {})
    # Keep unrecognized legacy attributes when editing a product in the same type.
    previous = existing or {}
    previous_type = previous.get('product_type') or infer_product_type(previous)
    same_type = previous.get('category') == product['category'] and previous_type == product['product_type']
    attributes = {key: value for key, value in (previous.get('attributes') or {}).items()
                  if same_type and (key not in FIELDS or key == 'brand')}
    product['attributes'] = attributes
    for field in allowed_types.get(product['product_type'], ()):
        value = request.form.get(field, '').strip()
        if value:
            attributes[field] = [size.strip() for size in value.split(',') if size.strip()] if field == 'size' else value

    try:
        price = float(product['price'])
        stock = int(product['stock'])
        if not product['name'] or product['product_type'] not in allowed_types or not isfinite(price) or price < 0 or not 0 <= stock < 2**63:
            raise ValueError
        if 'warranty_months' in attributes:
            warranty = int(attributes['warranty_months'])
            if not 0 <= warranty < 2**63:
                raise ValueError
            attributes['warranty_months'] = warranty
    except ValueError:
        return render_form(error=True), 400

    upload = request.files.get('image')
    if upload and upload.filename:
        limit = 5 * 1024 * 1024
        data = upload.stream.read(limit + 1)
        try:
            if len(data) > limit:
                raise ValueError
            with Image.open(BytesIO(data), formats=('JPEG', 'PNG', 'WEBP')) as image:
                if image.width * image.height > 20_000_000:
                    raise ValueError
                mime = Image.MIME[image.format]
                image.verify()
            with Image.open(BytesIO(data), formats=('JPEG', 'PNG', 'WEBP')) as image:
                image.load()
        except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
            return render_form(image_error=True), 400
        product['uploaded_image'] = {'data': data, 'mime': mime}

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
