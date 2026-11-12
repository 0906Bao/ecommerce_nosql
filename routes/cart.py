from flask import Blueprint, render_template, redirect, url_for, session, request
from database.connection import db
from bson.objectid import ObjectId
from datetime import datetime

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

        if product:
            subtotal = product['price'] * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

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

@cart_bp.route('/cart/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart.view_cart'))

    items = []
    total_amount = 0

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

        if product:
            item_total = product['price'] * quantity
            total_amount += item_total
            items.append({
                'product_id': str(product['_id']),
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'subtotal': item_total
            })

    # Lưu hóa đơn dưới dạng Embedded Documents vào collection 'hoadon'
    order = {
        'customer_name': request.form.get('customer_name', 'Khách hàng'),
        'phone': request.form.get('phone', ''),
        'address': request.form.get('address', ''),
        'items': items,
        'total_amount': total_amount,
        'created_at': datetime.now()
    }

    db.hoadon.insert_one(order)

    # Xóa giỏ hàng sau khi đặt thành công
    session['cart'] = {}
    session.modified = True

    return render_template('checkout_success.html', order=order)