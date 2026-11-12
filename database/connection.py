import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load các biến môi trường từ file .env
load_dotenv()

# Lấy chuỗi kết nối MONGO_URI, nếu không có thì dùng mặc định localhost
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/ecommerce_nosql")
MONGO_DB = os.getenv("MONGO_DB", "ecommerce_nosql")

# Khởi tạo MongoClient
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

# Chỉ định database chính cho đồ án
db = client[MONGO_DB]


def get_db():
    """Hàm trả về đối tượng database cho các Blueprint"""
    return db


def ping_mongo():
    """Kiểm tra khả năng kết nối MongoDB."""
    client.admin.command("ping")
    return True


def close_mongo(exception=None):
    """Hàm hỗ trợ đóng kết nối."""
    client.close()