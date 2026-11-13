from flask import Blueprint, render_template, request, redirect, url_for, session
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

        # 1. Kiểm tra tài khoản Admin mẫu
        if login_id == 'admin' and password == '123456':
            session['user'] = 'Quản trị viên'
            session['role'] = 'admin'
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

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
