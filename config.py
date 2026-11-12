import os


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    MONGO_DB = os.getenv("MONGO_DB", "ecommerce_nosql")
