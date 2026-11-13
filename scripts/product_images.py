import argparse

from catalog_images import catalog_image, is_seed_placeholder
from database.connection import db


def backfill_images(collection, apply=False):
    matched = updated = 0
    for product in collection.find({}, {"name": 1, "image": 1, "image_url": 1}):
        name = product.get("name")
        current = product.get("image")
        if product.get("image_url") or (current and not is_seed_placeholder(current)):
            continue
        image = catalog_image(name) if isinstance(name, str) else None
        if image:
            matched += 1
            if apply:
                updated += collection.update_one(
                    {"_id": product["_id"], "name": name, "image": current,
                     "image_url": product.get("image_url")},
                    {"$set": {"image": image}},
                ).modified_count
    return matched, updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign catalog photos using product names.")
    parser.add_argument("--apply", action="store_true", help="Save matches to MongoDB")
    args = parser.parse_args()
    matched, updated = backfill_images(db.sanpham, args.apply)
    print(f"Database: {db.name}. Matched: {matched}. Updated: {updated}.")
