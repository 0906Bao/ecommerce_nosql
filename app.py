import os
from flask import Flask, render_template
from dotenv import load_dotenv
from pymongo.errors import PyMongoError

# Load biến môi trường đầu tiên
load_dotenv()

from database.connection import close_mongo
from routes.auth import auth_bp, current_customer
from routes.recommendations import recommend_products
from routes.products import products_bp
from routes.categories import categories_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.admin import admin_bp
from routes.reviews import reviews_bp
from routes.info import info_bp  # <--- 1. Import blueprint thông tin tiện ích

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    app.config["MONGO_DB"] = os.getenv("MONGO_DB", "ecommerce_nosql")

    # 2. Đăng ký blueprint bên trong factory function (nơi biến app đã tồn tại)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(info_bp)

    @app.get("/")
    def home():
        try:
            customer = current_customer()
            recommendations, personalized = recommend_products(customer["_id"] if customer else None)
        except PyMongoError:
            app.logger.exception("Could not load homepage recommendations")
            recommendations, personalized = [], False
        return render_template(
            "home.html", title="E-commerce đa ngành hàng",
            recommendations=recommendations, personalized=personalized,
        )

    @app.get("/health")
    def health():
        from database.connection import ping_mongo
        try:
            ping_mongo()
            return {"status": "ok", "database": "connected"}, 200
        except Exception:
            app.logger.exception("MongoDB health check failed")
            return {"status": "error", "database": "disconnected"}, 503

    @app.teardown_appcontext
    def teardown_db(exception=None):
        # MongoClient is a shared connection pool; do not close it per request.
        pass

    return app

# Khởi tạo ứng dụng app từ factory
app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        use_reloader=False,
    )
