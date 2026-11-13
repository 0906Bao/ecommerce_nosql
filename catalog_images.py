import re
import unicodedata


PRODUCT_IMAGES = {
    "Laptop Dell": "laptop", "Smartphone Samsung": "smartphone",
    "Tai nghe Bluetooth": "headphones", "Bàn phím cơ": "keyboard",
    "Màn hình LG": "monitor", "Loa JBL": "speaker",
    "Chuột không dây": "mouse", "Ổ cứng SSD 1TB": "ssd",
    "Áo khoác dù": "jacket", "Quần Jeans nam": "jeans",
    "Áo thun Polo": "polo", "Giày Sneaker": "sneakers",
    "Balo thể thao": "backpack", "Nón kết": "cap",
    "Váy đầm nữ": "dress", "Áo sơ mi": "shirt",
    "Nồi cơm điện": "rice-cooker", "Máy xay sinh tố": "blender",
    "Quạt điều hòa": "air-cooler", "Bình đun siêu tốc": "kettle",
    "Lò vi sóng": "microwave", "Bộ nồi inox": "cookware",
    "Đèn bàn LED": "desk-lamp", "Máy lọc không khí": "air-purifier",
}


def catalog_image(name):
    name = unicodedata.normalize("NFC", name).strip().casefold()
    for prefix, filename in PRODUCT_IMAGES.items():
        prefix = prefix.casefold()
        if name == prefix or name.startswith(prefix + " "):
            return f"catalog/{filename}.webp"
    return None


def product_image(product):
    image = product.get("image_url") or product.get("image")
    if image and not is_seed_placeholder(image):
        return image
    return catalog_image(product.get("name") or "")


def is_seed_placeholder(image):
    return re.fullmatch(r"product_\d+\.jpg", str(image)) is not None
