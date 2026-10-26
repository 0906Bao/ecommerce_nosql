import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load các biến môi trường từ file .env
load_dotenv()

# Lấy chuỗi kết nối MONGO_URI, nếu không có thì dùng mặc định localhost
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/ecommerce_nosql")

# Khởi tạo MongoClient
client = MongoClient(MONGO_URI)

# Chỉ định database chính cho đồ án
db = client['ecommerce_nosql']

def get_db():
    """Hàm trả về đối tượng database cho các Blueprint"""
    return db

def close_mongo(exception=None):
    """Hàm hỗ trợ đóng kết nối"""
    pass

def ping_mongo():
    """Kiểm tra kết nối đến MongoDB."""
    try:
        client.admin.command("ping")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False