from flask import Blueprint, render_template, request
from database.connection import db

products_bp = Blueprint('products', __name__)

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
    categories = db.sanpham.distinct('category')

    return render_template(
        'products.html',
        products=products,
        categories=categories,
        selected_category=selected_category,
        search_keyword=search_keyword
    )