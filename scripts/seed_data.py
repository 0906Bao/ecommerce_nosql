import argparse
import random
from datetime import datetime, timedelta, timezone

from database.connection import client
from catalog_images import catalog_image


CATEGORIES = ("Điện tử", "Thời trang", "Gia dụng")


REVIEW_COMMENTS = {
    1: ("Sản phẩm nhận được chưa đúng như mong đợi.", "Trải nghiệm sử dụng chưa tốt."),
    2: ("Sản phẩm dùng được nhưng chất lượng chưa như kỳ vọng.", "Đóng gói ổn, chất lượng cần cải thiện."),
    3: ("Sản phẩm đúng mô tả, chất lượng ở mức ổn.", "Giá hợp lý, cần dùng thêm để đánh giá."),
    4: ("Sản phẩm đúng mô tả, đóng gói cẩn thận.", "Dùng khá tốt và phù hợp với giá."),
    5: ("Rất hài lòng, sản phẩm đúng như mô tả.", "Giao hàng nhanh, chất lượng tốt."),
}


def seed_reviews(database_name):
    if not database_name.startswith("ecommerce_demo_"):
        raise ValueError("Use an isolated database named ecommerce_demo_*.")

    db = client[database_name]
    now = datetime.now(timezone.utc)
    inserted = 0
    for product in db.sanpham.find({}, {"_id": 1}):
        product_id = product["_id"]
        existing = db.reviews.count_documents({"product_id": product_id}, limit=10)
        if existing >= 3:
            continue

        target = random.randint(3, 10)
        for index in range(target - existing):
            rating = random.choices(range(1, 6), weights=(1, 2, 5, 12, 15))[0]
            result = db.reviews.update_one(
                {"_id": f"demo-review:{type(product_id).__name__}:{product_id}:{index}"},
                {"$setOnInsert": {
                    "product_id": product_id,
                    "customer_name": f"Khách hàng mẫu {index + 1}",
                    "rating": rating,
                    "content": random.choice(REVIEW_COMMENTS[rating]),
                    "created_at": now - timedelta(days=random.randint(0, 30)),
                }},
                upsert=True,
            )
            inserted += result.upserted_id is not None

    print(f"Đã thêm {inserted} đánh giá mẫu.")
    return inserted


def seed_database(database_name, product_count=100, order_count=50):
    if not database_name.startswith("ecommerce_demo_"):
        raise ValueError("Use an isolated database named ecommerce_demo_*.")
    if product_count < 5 or order_count < 1:
        raise ValueError("Use at least 5 products and 1 order.")

    db = client[database_name]
    if any(db[name].find_one() is not None for name in ("danhmuc", "sanpham", "hoadon")):
        raise ValueError("Demo database already contains data. Choose a fresh database name.")

    now = datetime.now(timezone.utc)
    db.danhmuc.insert_many([{"ten": name} for name in CATEGORIES])

    # Danh sách dữ liệu mẫu theo ngành hàng để trộn ngẫu nhiên
    elec_names = ["Laptop Dell", "Smartphone Samsung", "Tai nghe Bluetooth", "Bàn phím cơ", "Màn hình LG", "Loa JBL", "Chuột không dây", "Ổ cứng SSD 1TB"]
    fashion_names = ["Áo khoác dù", "Quần Jeans nam", "Áo thun Polo", "Giày Sneaker", "Balo thể thao", "Nón kết", "Váy đầm nữ", "Áo sơ mi"]
    home_names = ["Nồi cơm điện", "Máy xay sinh tố", "Quạt điều hòa", "Bình đun siêu tốc", "Lò vi sóng", "Bộ nồi inox", "Đèn bàn LED", "Máy lọc không khí"]

    products = []

    # 1. Sinh sản phẩm (Polymorphic Schema)
    for i in range(1, product_count + 1):
        cat = CATEGORIES[(i - 1) % len(CATEGORIES)]
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
            "image": catalog_image(name),
            "attributes": attributes,
            "created_at": now - timedelta(days=random.randint(1, 30))
        }
        products.append(product_doc)

    # Insert vào collection sanpham
    insert_result = db.sanpham.insert_many(products)
    product_ids = insert_result.inserted_ids
    print(f" Đã nạp thành công {len(product_ids)} sản phẩm vào collection 'sanpham'.")

    # 2. Sinh đơn hàng (Embedded Documents)
    orders = []
    customer_names = ["Nguyen Van A", "Tran Thi B", "Le Van C", "Pham Thi D", "Hoang Van E", "Vu Thị F"]

    for _ in range(order_count):
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
                "product_id": str(p["_id"]),
                "category": p["category"],
                "attributes": p["attributes"],
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
            "created_at": now - timedelta(days=random.randint(0, 10))
        }
        orders.append(order_doc)

    db.hoadon.insert_many(orders)
    seed_reviews(database_name)
    print(f" Đã nạp thành công {len(orders)} đơn hàng (có nhúng sản phẩm) vào collection 'hoadon'.")
    print(" Hoàn tất nạp toàn bộ dữ liệu mẫu!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Database named ecommerce_demo_*")
    parser.add_argument("--products", type=int, default=100)
    parser.add_argument("--orders", type=int, default=50)
    parser.add_argument("--reviews-only", action="store_true", help="Add reviews to existing demo products")
    args = parser.parse_args()
    try:
        if args.reviews_only:
            seed_reviews(args.db)
        else:
            seed_database(args.db, args.products, args.orders)
    except ValueError as error:
        parser.error(str(error))