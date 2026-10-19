from pymongo import ASCENDING, DESCENDING
from database.connection import get_db


def create_indexes():
    db = get_db()
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.sanpham.create_index([("danh_muc", ASCENDING), ("gia", ASCENDING)])
    db.sanpham.create_index([("ten", ASCENDING)])
    db.hoadon.create_index([("trang_thai", ASCENDING), ("ngay_dat", DESCENDING)])
    db.danhgia.create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])
    print("Đã tạo/kiểm tra các index cơ bản.")
