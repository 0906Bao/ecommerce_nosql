from secrets import token_hex

from bson import ObjectId
from bson.errors import InvalidId
from flask import abort, Blueprint, render_template, request, Response, session, url_for
from catalog_images import product_image
from database.connection import db
from product_types import FIELDS, infer_product_type, product_type_options
from routes.auth import current_customer
from routes.orders import has_purchased_product
from routes.categories import category_names

products_bp = Blueprint('products', __name__)
PRICE_RANGES = {
    'under_500k': ('Dưới 500.000 đ', {'$lt': 500_000}),
    '500k_to_1m': ('500.000 đ – dưới 1.000.000 đ', {'$gte': 500_000, '$lt': 1_000_000}),
    '1m_to_2m': ('1.000.000 đ – dưới 2.000.000 đ', {'$gte': 1_000_000, '$lt': 2_000_000}),
    '2m_to_5m': ('2.000.000 đ – dưới 5.000.000 đ', {'$gte': 2_000_000, '$lt': 5_000_000}),
    '5m_and_up': ('Từ 5.000.000 đ', {'$gte': 5_000_000}),
}


@products_bp.app_context_processor
def product_image_context():
    def image_source(product):
        if product.get('uploaded_image'):
            return url_for('products.uploaded_image', product_id=product['_id'])
        image = product_image(product)
        if image and not image.startswith(('http://', 'https://')):
            return url_for('static', filename='images/' + image)
        return image

    return {'product_image': image_source}

def rating_summaries(product_ids):
    if not product_ids:
        return {}
    return {
        row['_id']: row
        for row in db.reviews.aggregate([
            {'$match': {'product_id': {'$in': product_ids}, 'rating': {'$in': [1, 2, 3, 4, 5]}}},
            {'$group': {'_id': '$product_id', 'average': {'$avg': '$rating'}, 'count': {'$sum': 1}}},
        ])
    }


def sold_quantities(product_ids):
    if not product_ids:
        return {}
    # Seed and checkout may store the same product ID using different BSON types.
    ids = list(dict.fromkeys([*product_ids, *(str(value) for value in product_ids)]))
    return {
        row['_id']: row['sold']
        for row in db.hoadon.aggregate([
            {'$match': {'items.product_id': {'$in': ids}}},
            {'$unwind': '$items'},
            {'$match': {'items.product_id': {'$in': ids}}},
            {'$group': {'_id': {'$toString': '$items.product_id'}, 'sold': {'$sum': '$items.quantity'}}},
        ])
    }


@products_bp.route('/products')
def list_products():
    selected_category = request.args.get('category')
    search_keyword = request.args.get('q', '').strip()
    categories = category_names()
    type_options = {
        category: product_type_options(category)
        for category in categories
        if not selected_category or category == selected_category
    }
    selected_type = request.args.get('product_type')
    if not any(selected_type in options for options in type_options.values()):
        selected_type = None

    query = {}
    if selected_category:
        query['category'] = selected_category

    # Xử lý tìm kiếm sản phẩm theo tên (không phân biệt hoa thường với $regex)
    if search_keyword:
        query['name'] = {'$regex': search_keyword, '$options': 'i'}

    filters = {}
    for field in ('min_price', 'max_price', 'min_sold', 'max_sold', 'min_rating'):
        value = request.args.get(field, type=int)
        if value is not None and 0 <= value <= 2**63 - 1:
            filters[field] = value

    selected_price = request.args.get('price_range')
    price_range = {
        operator: filters[field]
        for operator, field in (('$gte', 'min_price'), ('$lte', 'max_price'))
        if field in filters
    }
    if selected_price in PRICE_RANGES:
        price_range = PRICE_RANGES[selected_price][1]
        filters.pop('min_price', None)
        filters.pop('max_price', None)
        filters['price_range'] = selected_price
    if price_range:
        query['price'] = price_range

    products = list(db.sanpham.find(query, {'uploaded_image.data': 0}).sort('_id', 1))
    if selected_type:
        products = [
            product for product in products
            if (product.get('product_type') or infer_product_type(product)) == selected_type
        ]
    product_ids = [product['_id'] for product in products]
    ratings = rating_summaries(product_ids)
    sold_counts = sold_quantities(product_ids)

    def average(product):
        return ratings.get(product['_id'], {}).get('average', 0)

    def sold(product):
        return sold_counts.get(str(product['_id']), 0)

    products = [
        product for product in products
        if average(product) >= filters.get('min_rating', 0)
        and filters.get('min_sold', 0) <= sold(product) <= filters.get('max_sold', float('inf'))
    ]
    sort = request.args.get('sort', '')
    field, _, direction = sort.partition('_')
    sort_keys = {'price': lambda product: product['price'], 'rating': average, 'sold': sold}
    if field in sort_keys and direction in ('asc', 'desc'):
        products.sort(key=sort_keys[field], reverse=direction == 'desc')
        filters['sort'] = sort

    total = len(products)
    per_page = 20
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(pages, max(1, request.args.get('page', 1, type=int)))
    start = (page - 1) * per_page
    link_filters = dict(filters)
    if search_keyword:
        link_filters['q'] = search_keyword
    page_filters = dict(link_filters)
    if selected_type:
        page_filters['product_type'] = selected_type
    if selected_category:
        page_filters['category'] = selected_category

    return render_template(
        'products.html',
        products=products[start:start + per_page],
        ratings=ratings,
        sold_counts=sold_counts,
        categories=categories,
        type_options=type_options,
        selected_type=selected_type,
        selected_category=selected_category,
        search_keyword=search_keyword,
        filters=filters,
        price_ranges=PRICE_RANGES,
        link_filters=link_filters,
        page_filters=page_filters,
        page=page,
        pages=pages,
        total=total,
    )

def find_product(collection, product_id, projection=None):
    candidates = [product_id]
    try:
        candidates.insert(0, ObjectId(product_id))
    except InvalidId:
        pass
    if product_id.isascii() and product_id.isdecimal() and len(product_id) <= 18:
        candidates.append(int(product_id))
    for candidate in candidates:
        product = collection.find_one({'_id': candidate}, projection)
        if product is not None:
            return product
    abort(404)

@products_bp.get('/products/<product_id>/image')
def uploaded_image(product_id):
    product = find_product(db.sanpham, product_id, {'uploaded_image': 1})
    image = product.get('uploaded_image')
    if not image:
        abort(404)
    response = Response(image['data'], mimetype=image['mime'])
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@products_bp.get('/products/<product_id>')
def product_detail(product_id):
    product = find_product(db.sanpham, product_id, {'uploaded_image.data': 0})
    category = product.get('category') or product.get('category_name')
    related_products = []
    if category:
        related_products = list(db.sanpham.find({
            'category': category,
            '_id': {'$ne': product['_id']},
        }, {'uploaded_image.data': 0}).sort('name', 1).limit(4))
    reviews = list(db.reviews.find({'product_id': product['_id']}).sort('created_at', -1))
    customer = current_customer()
    can_review = customer is not None and has_purchased_product(customer['_id'], product['_id'])
    csrf_token = session.setdefault('review_csrf', token_hex(32)) if can_review else None
    return render_template('product_detail.html', product=product, category=category, field_labels=FIELDS,
                           related_products=related_products, reviews=reviews,
                           sold=sold_quantities([product['_id']]).get(str(product['_id']), 0),
                           rating=rating_summaries([product['_id']]).get(product['_id']),
                           can_review=can_review, review_csrf_token=csrf_token)
