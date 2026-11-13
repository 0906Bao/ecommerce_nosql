from flask import Blueprint, render_template, redirect, url_for, session, request, flash, current_app
from database.connection import db
from routes.auth import current_customer
from bson.objectid import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from werkzeug.exceptions import NotFound
from routes.products import find_product
from datetime import datetime, timezone

cart_bp = Blueprint('cart', __name__)

def clean_id(product_id):
    if not product_id:
        return ""
    return str(product_id).replace("ObjectId(", "").replace("'", "").replace('"', "").replace(")", "").strip()

@cart_bp.route('/cart', endpoint='view_cart')
@cart_bp.route('/cart/', endpoint='view_cart_slash')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0

    for raw_id, quantity in cart.items():
        product_id = clean_id(raw_id)
        product = None
        try:
            product = db.sanpham.find_one({'_id': ObjectId(product_id)})
        except Exception:
            pass
        if not product:
            product = db.sanpham.find_one({'_id': product_id})
        if not product:
            try:
                product = db.sanpham.find_one({'_id': int(product_id)})
            except Exception:
                pass

        if not product:
            product = {'_id': product_id, 'name': 'Sản phẩm không còn được bán', 'price': 0, 'stock': 0}
        if product:
            subtotal = product['price'] * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

    customer = current_customer() if cart_items else None
    return render_template('cart.html', cart_items=cart_items, total_price=total_price, customer=customer or {})

@cart_bp.route('/cart/add/<product_id>', methods=['POST', 'GET'])
def add_to_cart(product_id):
    clean_product_id = clean_id(product_id)
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    if clean_product_id in cart:
        cart[clean_product_id] += 1
    else:
        cart[clean_product_id] = 1

    session['cart'] = cart
    session.modified = True  # Bắt buộc để lưu session
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/decrease/<product_id>')
def decrease_cart(product_id):
    clean_product_id = clean_id(product_id)
    cart = session.get('cart', {})

    if clean_product_id in cart:
        if cart[clean_product_id] > 1:
            cart[clean_product_id] -= 1
        else:
            del cart[clean_product_id]

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/remove/<product_id>')
def remove_from_cart(product_id):
    clean_product_id = clean_id(product_id)
    cart = session.get('cart', {})
    if clean_product_id in cart:
        del cart[clean_product_id]
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart.view_cart'))

class StockUnavailable(Exception):
    pass


def restore_stock(reserved):
    for product_id, quantity in reversed(reserved):
        db.sanpham.update_one({'_id': product_id}, {'$inc': {'stock': quantity}})


@cart_bp.route('/cart/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart.view_cart'))

    customer = current_customer()
    quantities = {}
    for raw_id, quantity in cart.items():
        try:
            product = find_product(db.sanpham, clean_id(raw_id))
        except NotFound:
            flash('Có sản phẩm không còn được bán. Vui lòng cập nhật giỏ hàng.', 'cart_error')
            return redirect(url_for('cart.view_cart'))
        if type(quantity) is not int or not 0 < quantity < 2**63:
            flash('Số lượng trong giỏ hàng không hợp lệ.', 'cart_error')
            return redirect(url_for('cart.view_cart'))
        product_id = product['_id']
        quantities[product_id] = quantities.get(product_id, 0) + quantity

    order = {
        '_id': ObjectId(),
        'customer_name': request.form.get('customer_name', 'Khách hàng'),
        'phone': request.form.get('phone', ''),
        'address': request.form.get('address', ''),
        'items': [],
        'created_at': datetime.now(timezone.utc),
    }
    if customer is not None:
        order['customer_id'] = customer['_id']

    reserved = []
    try:
        for product_id, quantity in quantities.items():
            product = db.sanpham.find_one_and_update(
                {'_id': product_id, 'stock': {'$gte': quantity}},
                {'$inc': {'stock': -quantity}},
                return_document=ReturnDocument.BEFORE,
            )
            if product is None:
                raise StockUnavailable
            reserved.append((product_id, quantity))
            order['items'].append({
                'product_id': str(product_id),
                'name': product['name'],
                'category': product.get('category'),
                'attributes': product.get('attributes', {}),
                'price_at_purchase': product['price'],
                'quantity': quantity,
                'subtotal': product['price'] * quantity,
            })

        order['total_amount'] = sum(item['subtotal'] for item in order['items'])
        db.hoadon.insert_one(order)
    except StockUnavailable:
        restore_stock(reserved)
        flash('Có sản phẩm không đủ tồn kho. Vui lòng giảm số lượng và thử lại.', 'cart_error')
        return redirect(url_for('cart.view_cart'))
    except PyMongoError:
        current_app.logger.exception('Checkout write failed')
        # The insert may have succeeded before the connection dropped.
        if db.hoadon.find_one({'_id': order['_id']}) is None:
            restore_stock(reserved)
            flash('Chưa thể lưu đơn hàng. Vui lòng thử lại.', 'cart_error')
            return redirect(url_for('cart.view_cart'))

    session.pop('cart', None)
    return render_template('checkout_success.html', order=order)
