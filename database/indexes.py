from pymongo import ASCENDING, DESCENDING
from database.connection import get_db


def create_indexes():
    db = get_db()

    db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
    db.users.create_index([("phone", ASCENDING)], unique=True, sparse=True)
    db.users.create_index([("username", ASCENDING)], unique=True, sparse=True)

    db.sanpham.create_index([("category", ASCENDING), ("price", ASCENDING)])
    db.sanpham.create_index([("name", ASCENDING)])

    db.hoadon.create_index([("status", ASCENDING), ("created_at", DESCENDING)])

    db.reviews.create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])

    print("Đã tạo/kiểm tra các index cơ bản.")
