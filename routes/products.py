from secrets import token_hex

from bson import ObjectId
from bson.errors import InvalidId
from flask import abort, Blueprint, render_template, request, session
from catalog_images import product_image
from database.connection import db
from routes.auth import current_customer
from routes.categories import category_names

products_bp = Blueprint('products', __name__)


@products_bp.context_processor
def product_image_context():
    return {'product_image': product_image}

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

    query = {}
    if selected_category:
        query['category'] = selected_category

    # Xử lý tìm kiếm sản phẩm theo tên (không phân biệt hoa thường với $regex)
    if search_keyword:
        query['name'] = {'$regex': search_keyword, '$options': 'i'}

    products = list(db.sanpham.find(query))
    categories = category_names()
    product_ids = [product['_id'] for product in products]

    return render_template(
        'products.html',
        products=products,
        ratings=rating_summaries(product_ids),
        sold_counts=sold_quantities(product_ids),
        categories=categories,
        selected_category=selected_category,
        search_keyword=search_keyword
    )

def find_product(collection, product_id):
    candidates = [product_id]
    try:
        candidates.insert(0, ObjectId(product_id))
    except InvalidId:
        pass
    if product_id.isascii() and product_id.isdecimal() and len(product_id) <= 18:
        candidates.append(int(product_id))
    for candidate in candidates:
        product = collection.find_one({'_id': candidate})
        if product is not None:
            return product
    abort(404)


@products_bp.get('/products/<product_id>')
def product_detail(product_id):
    product = find_product(db.sanpham, product_id)
    category = product.get('category') or product.get('category_name')
    related_products = []
    if category:
        related_products = list(db.sanpham.find({
            'category': category,
            '_id': {'$ne': product['_id']},
        }).sort('name', 1).limit(4))
    reviews = list(db.reviews.find({'product_id': product['_id']}).sort('created_at', -1))
    can_review = current_customer() is not None
    csrf_token = session.setdefault('review_csrf', token_hex(32)) if can_review else None
    return render_template('product_detail.html', product=product, category=category,
                           related_products=related_products, reviews=reviews,
                           sold=sold_quantities([product['_id']]).get(str(product['_id']), 0),
                           rating=rating_summaries([product['_id']]).get(product['_id']),
                           can_review=can_review, review_csrf_token=csrf_token)
