import os
from hmac import compare_digest
from secrets import token_hex

from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import abort, flash, Blueprint, render_template, request, redirect, url_for, session
from database.connection import db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id')  # Email, SĐT hoặc username
        password = request.form.get('password')

        admin_password = os.getenv('ADMIN_PASSWORD')
        if login_id == 'admin' and admin_password and password and compare_digest(
            password.encode('utf-8'), admin_password.encode('utf-8')
        ):
            session['user'] = 'Quản trị viên'
            session['role'] = 'admin'
            session.pop('user_id', None)
            return redirect(url_for('admin.dashboard'))

        # 2. Kiểm tra trong MongoDB collection 'users'
        user = db.users.find_one({
            '$or': [{'email': login_id}, {'phone': login_id}, {'username': login_id}]
        })

        password_hash = (user.get('password') or user.get('password_hash')) if user else None
        if password_hash and password and check_password_hash(password_hash, password):
            session['user'] = user.get('name', user.get('email', 'Khách hàng'))
            session['role'] = 'customer'
            session['user_id'] = str(user['_id'])
            return redirect(url_for('products.list_products'))
        else:
            return render_template('login.html', error="Tài khoản hoặc mật khẩu không chính xác!")

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        login_contact = request.form.get('login_contact')  # Email hoặc SĐT
        password = request.form.get('password')
        if not password or password != request.form.get('confirm_password'):
            return render_template(
                'register.html', error="Vui lòng nhập mật khẩu và xác nhận mật khẩu trùng khớp!"
            )

        existing_user = db.users.find_one({
            '$or': [{'email': login_contact}, {'phone': login_contact}]
        })

        if existing_user:
            return render_template('register.html', error="Email hoặc Số điện thoại này đã được đăng ký!")

        is_email = '@' in login_contact
        user_data = {
            'name': name,
            ('email' if is_email else 'phone'): login_contact,
            'password': generate_password_hash(password),
            'role': 'customer'
        }

        db.users.insert_one(user_data)
        return redirect(url_for('auth.login'))

    return render_template('register.html')

def current_customer():
    user_id = session.get('user_id')
    if session.get('role') != 'customer' or not isinstance(user_id, str):
        return None

    projection = {'name': 1, 'email': 1, 'phone': 1, 'address': 1, 'shipping_address': 1}
    if ObjectId.is_valid(user_id):
        customer = db.users.find_one({'_id': ObjectId(user_id)}, projection)
        if customer is not None:
            return customer
    return db.users.find_one({'_id': user_id}, projection)


@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    customer = current_customer()
    if customer is None:
        return redirect(url_for('auth.login'))

    token = session.setdefault('profile_csrf', token_hex(32))
    if request.method == 'GET':
        return render_template('profile.html', customer=customer, csrf_token=token)

    if not compare_digest(token.encode(), request.form.get('csrf_token', '').encode()):
        abort(400)

    fields = {field: request.form.get(field, '').strip() for field in ('name', 'phone', 'address')}
    customer.update(fields)
    error = None
    if not fields['name'] or not fields['phone'] or any(
        len(fields[field]) > limit for field, limit in (('name', 120), ('phone', 32), ('address', 500))
    ):
        error = 'Vui lòng nhập họ tên và số điện thoại hợp lệ. Kiểm tra độ dài của các trường.'
    else:
        try:
            phone = fields['phone']
            duplicate = db.users.find_one({
                '_id': {'$ne': customer['_id']},
                '$or': [{'phone': phone}, {'email': phone}, {'username': phone}],
            }, {'_id': 1})
            if duplicate:
                raise DuplicateKeyError('Phone already in use')
            result = db.users.update_one(
                {'_id': customer['_id']}, {'$set': fields, '$unset': {'shipping_address': ''}}
            )
            if not result.matched_count:
                return redirect(url_for('auth.login'))
        except DuplicateKeyError:
            error = 'Số điện thoại này đã được tài khoản khác sử dụng.'
            return render_template('profile.html', customer=customer, csrf_token=token, error=error), 409
        session['user'] = fields['name']
        flash('Đã lưu thông tin cá nhân.')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', customer=customer, csrf_token=token, error=error), 400


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
