from flask import Blueprint, render_template

info_bp = Blueprint('info', __name__)

@info_bp.route('/khuyen-mai')
def promotions():
    return render_template('info.html', title="Chương Trình Khuyến Mãi", type="promo")

@info_bp.route('/tin-tuc')
def news():
    return render_template('info.html', title="Tin Tức & Review Công Nghệ", type="news")

@info_bp.route('/bao-hanh')
def warranty():
    return render_template('info.html', title="Tra Cứu Bảo Hành", type="warranty")

@info_bp.route('/dich-vu')
def services():
    return render_template('info.html', title="Dịch Vụ Tận Nhà", type="services")

@info_bp.route('/thu-cu')
def trade_in():
    return render_template('info.html', title="Thu Cũ Đổi Mới - Lên Đời Siêu Phẩm", type="tradein")

@info_bp.route('/showroom')
def showroom():
    return render_template('info.html', title="Hệ Thống Showroom Toàn Quốc", type="showroom")