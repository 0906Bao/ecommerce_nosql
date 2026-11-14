from collections import defaultdict
from datetime import datetime, timezone

from database.connection import db
from routes.products import rating_summaries, sold_quantities


def recency_weight(created_at, now):
    if not isinstance(created_at, datetime):
        return 0.5
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max(0, (now - created_at).days)
    return 1 / (1 + age_days / 90)


def customer_preferences(customer_id, products):
    now = datetime.now(timezone.utc)
    categories = {
        str(product["_id"]): product.get("category") or product.get("category_name")
        for product in products
    }
    purchase_scores = {}
    review_scores = {}
    for order in db.hoadon.find(
        {"customer_id": customer_id, "status": {"$nin": ["Cancelled", "Canceled", "Refunded"]}},
        {"items": 1, "created_at": 1},
    ):
        weight = recency_weight(order.get("created_at"), now)
        for item in order.get("items", []):
            if item.get("quantity", 0) <= 0 or item.get("product_id") is None:
                continue
            product_id = str(item["product_id"])
            purchase_scores[product_id] = min(2, purchase_scores.get(product_id, 0) + weight)
            if not categories.get(product_id):
                categories[product_id] = item.get("category")

    for review in db.reviews.find(
        {"user_id": customer_id, "rating": {"$in": [1, 2, 3, 4, 5]}},
        {"product_id": 1, "rating": 1, "created_at": 1},
    ).sort([("created_at", -1), ("_id", -1)]):
        product_id = str(review["product_id"])
        score = (review["rating"] - 3) * recency_weight(review.get("created_at"), now)
        review_scores.setdefault(product_id, score)

    preferences = defaultdict(float)
    for product_id in purchase_scores.keys() | review_scores.keys():
        category = categories.get(product_id)
        if category:
            preferences[category] += purchase_scores.get(product_id, 0) + review_scores.get(product_id, 0)
    return preferences, purchase_scores.keys(), review_scores


def recommend_products(customer_id=None, limit=6):
    catalog = list(db.sanpham.find({}, {
        "name": 1, "price": 1, "category": 1, "category_name": 1,
        "stock": 1, "image": 1, "uploaded_image.content_type": 1,
    }))
    preferences, purchased, reviewed = {}, (), {}
    if customer_id is not None:
        preferences, purchased, reviewed = customer_preferences(customer_id, catalog)
    personalized = any(preferences.values())

    candidates = [
        product for product in catalog
        if product.get("stock", 0) > 0
        and str(product["_id"]) not in purchased
        and reviewed.get(str(product["_id"]), 0) >= 0
    ]
    ids = [product["_id"] for product in candidates]
    ratings = rating_summaries(ids)
    sales = sold_quantities(ids)

    def rank(product):
        product_id = product["_id"]
        category = product.get("category") or product.get("category_name")
        rating = ratings.get(product_id, {})
        count = rating.get("count", 0)
        adjusted_rating = (rating.get("average", 0) * count + 3 * 5) / (count + 5)
        return (
            -preferences.get(category, 0),
            -sales.get(str(product_id), 0) if not personalized else 0,
            -adjusted_rating,
            -sales.get(str(product_id), 0),
            str(product_id),
        )

    return sorted(candidates, key=rank)[:limit], personalized
