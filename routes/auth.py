from flask import Blueprint, render_template

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login():
    return render_template("placeholder.html", title="Đăng nhập", message="Chức năng đăng nhập sẽ được triển khai tiếp.")


@auth_bp.get("/register")
def register():
    return render_template("placeholder.html", title="Đăng ký", message="Chức năng đăng ký sẽ được triển khai tiếp.")
