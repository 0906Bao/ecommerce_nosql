import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ecommerce_db')
client = MongoClient(mongo_uri)
db = client["ecommerce_nosql"]

def seed_database():
    print("🚀 Bắt đầu quá trình sinh dữ liệu mẫu (Dummy Data)...")

    # Xóa dữ liệu cũ nếu có (hoặc comment lại nếu muốn giữ)
    db.sanpham.delete_many({})
    db.hoadon.delete_many({})

    categories = ["Điện tử", "Thời trang", "Gia dụng"]

    # Danh sách dữ liệu mẫu theo ngành hàng để trộn ngẫu nhiên
    elec_names = ["Laptop Dell", "Smartphone Samsung", "Tai nghe Bluetooth", "Bàn phím cơ", "Màn hình LG", "Loa JBL", "Chuột không dây", "Ổ cứng SSD 1TB"]
    fashion_names = ["Áo khoác dù", "Quần Jeans nam", "Áo thun Polo", "Giày Sneaker", "Balo thể thao", "Nón kết", "Váy đầm nữ", "Áo sơ mi"]
    home_names = ["Nồi cơm điện", "Máy xay sinh tố", "Quạt điều hòa", "Bình đun siêu tốc", "Lò vi sóng", "Bộ nồi inox", "Đèn bàn LED", "Máy lọc không khí"]

    products = []

    # 1. Sinh 100 sản phẩm (Polymorphic Schema)
    for i in range(1, 101):
        cat = random.choice(categories)
        if cat == "Điện tử":
            name = f"{random.choice(elec_names)} Gen {i}"
            price = random.randint(2000000, 25000000)
            attributes = {
                "cpu": random.choice(["Intel Core i5", "Apple M2", "AMD Ryzen 5"]),
                "ram": random.choice(["8GB", "16GB", "32GB"]),
                "warranty_months": random.choice([12, 24])
            }
        elif cat == "Thời trang":
            name = f"{random.choice(fashion_names)} V{i}"
            price = random.randint(150000, 1200000)
            attributes = {
                "size": random.choice([["S", "M", "L"], ["M", "L", "XL"], ["FreeSize"]]),
                "color": random.choice([["Đen", "Trắng"], ["Xanh", "Đỏ"], ["Xám", "Nâu"]]),
                "material": random.choice(["Cotton 100%", "Polyester", "Kaki"])
            }
        else:
            name = f"{random.choice(home_names)} Pro {i}"
            price = random.randint(300000, 4500000)
            attributes = {
                "power": random.choice(["500W", "800W", "1200W", "1500W"]),
                "origin": random.choice(["Việt Nam", "Nhật Bản", "Hàn Quốc", "Trung Quốc"]),
                "capacity": random.choice(["1.5L", "2L", "5L", "Không áp dụng"])
            }

        product_doc = {
            "name": name,
            "category": cat,
            "price": price,
            "stock": random.randint(10, 100),
            "image": f"product_{i}.jpg",
            "attributes": attributes,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30))
        }
        products.append(product_doc)

    # Insert vào collection sanpham
    insert_result = db.sanpham.insert_many(products)
    product_ids = insert_result.inserted_ids
    print(f" Đã nạp thành công {len(product_ids)} sản phẩm vào collection 'sanpham'.")

    # 2. Sinh 50 đơn hàng (Embedded Documents)
    orders = []
    customer_names = ["Nguyen Van A", "Tran Thi B", "Le Van C", "Pham Thi D", "Hoang Van E", "Vu Thị F"]

    for i in range(1, 51):
        # Chọn ngẫu nhiên từ 2 đến 5 sản phẩm cho mỗi đơn hàng
        num_items = random.randint(2, 5)
        chosen_products = random.sample(products, num_items)

        order_items = []
        total_amount = 0

        for p in chosen_products:
            # Lấy ID thực tế từ database của sản phẩm đó
            # (Tìm lại trong db hoặc gán qua danh sách trên)
            qty = random.randint(1, 3)
            subtotal = p["price"] * qty
            total_amount += subtotal

            order_items.append({
                "product_id": p.get("_id"),
                "name": p["name"],
                "price_at_purchase": p["price"], # Lưu giá cố định tại thời điểm mua
                "quantity": qty,
                "subtotal": subtotal
            })

        order_doc = {
            "customer_name": random.choice(customer_names),
            "shipping_address": f"Số {random.randint(1, 200)} Đường Lê Văn Việt, TP. Thủ Đức",
            "total_amount": total_amount,
            "status": random.choice(["Processing", "Shipping", "Completed"]),
            "items": order_items, # Embedded mảng sản phẩm
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 10))
        }
        orders.append(order_doc)

    db.hoadon.insert_many(orders)
    print(f" Đã nạp thành công {len(orders)} đơn hàng (có nhúng sản phẩm) vào collection 'hoadon'.")
    print(" Hoàn tất nạp toàn bộ dữ liệu mẫu!")

if __name__ == "__main__":
    seed_database()