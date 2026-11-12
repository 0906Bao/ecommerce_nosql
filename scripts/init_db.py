from dotenv import load_dotenv
from flask import Flask
from database.indexes import create_indexes

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = __import__("os").getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
app.config["MONGO_DB"] = __import__("os").getenv("MONGO_DB", "ecommerce_nosql")

with app.app_context():
    from database.connection import ping_mongo
    ping_mongo()
    create_indexes()
    print(f"MongoDB sẵn sàng: {app.config['MONGO_DB']}")
