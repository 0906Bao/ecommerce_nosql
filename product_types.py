import re


FIELDS = {
    'brand': 'Thương hiệu',
    'cpu': 'CPU',
    'ram': 'RAM',
    'storage': 'Dung lượng lưu trữ',
    'warranty_months': 'Bảo hành (tháng)',
    'screen': 'Kích thước màn hình',
    'resolution': 'Độ phân giải',
    'connection': 'Kết nối',
    'battery': 'Thời lượng pin',
    'switch': 'Loại switch',
    'dpi': 'Độ nhạy (DPI)',
    'interface': 'Chuẩn giao tiếp',
    'color': 'Màu sắc',
    'material': 'Chất liệu',
    'size': 'Kích cỡ (phân cách bằng dấu phẩy)',
    'dimensions': 'Kích thước',
    'capacity': 'Dung tích',
    'power': 'Công suất',
    'origin': 'Xuất xứ',
    'pieces': 'Số món',
    'filter_type': 'Loại bộ lọc',
    'coverage': 'Diện tích sử dụng',
    'light_color': 'Màu ánh sáng',
}

FASHION_FIELDS = ('size', 'material', 'color')
APPLIANCE_FIELDS = ('capacity', 'power', 'origin')
COMPUTER_FIELDS = ('cpu', 'ram', 'storage', 'screen', 'warranty_months')

# Each entry pairs the demo name prefix with the fields for that type.
PRODUCT_TYPES = {
    'Điện tử': {
        'Laptop': ('Laptop Dell', COMPUTER_FIELDS),
        'Điện thoại': ('Smartphone Samsung', COMPUTER_FIELDS + ('battery',)),
        'Tai nghe': ('Tai nghe Bluetooth', ('connection', 'battery', 'warranty_months')),
        'Bàn phím': ('Bàn phím cơ', ('switch', 'connection', 'warranty_months')),
        'Màn hình': ('Màn hình LG', ('screen', 'resolution', 'connection', 'warranty_months')),
        'Loa': ('Loa JBL', ('power', 'connection', 'battery', 'warranty_months')),
        'Chuột': ('Chuột không dây', ('dpi', 'connection', 'warranty_months')),
        'Ổ cứng SSD': ('Ổ cứng SSD 1TB', ('storage', 'interface', 'warranty_months')),
    },
    'Thời trang': {
        'Áo khoác': ('Áo khoác dù', FASHION_FIELDS),
        'Quần jeans': ('Quần Jeans nam', FASHION_FIELDS),
        'Áo polo': ('Áo thun Polo', FASHION_FIELDS),
        'Giày sneaker': ('Giày Sneaker', FASHION_FIELDS),
        'Balo': ('Balo thể thao', ('dimensions', 'capacity', 'material', 'color')),
        'Nón': ('Nón kết', FASHION_FIELDS),
        'Váy đầm': ('Váy đầm nữ', FASHION_FIELDS),
        'Áo sơ mi': ('Áo sơ mi', FASHION_FIELDS),
    },
    'Gia dụng': {
        'Nồi cơm điện': ('Nồi cơm điện', APPLIANCE_FIELDS),
        'Máy xay sinh tố': ('Máy xay sinh tố', APPLIANCE_FIELDS),
        'Quạt điều hòa': ('Quạt điều hòa', APPLIANCE_FIELDS + ('coverage',)),
        'Bình đun siêu tốc': ('Bình đun siêu tốc', APPLIANCE_FIELDS),
        'Lò vi sóng': ('Lò vi sóng', APPLIANCE_FIELDS),
        'Bộ nồi': ('Bộ nồi inox', ('pieces', 'material', 'origin')),
        'Đèn bàn': ('Đèn bàn LED', ('power', 'light_color', 'origin')),
        'Máy lọc không khí': ('Máy lọc không khí', ('power', 'filter_type', 'coverage', 'origin')),
    },
}


def product_type_options(category):
    return {
        **{label: fields for label, (_, fields) in PRODUCT_TYPES.get(category, {}).items()},
        'Khác': (),
    }


def infer_product_type(product):
    name = (product.get('name') or '').casefold()
    for label, (prefix, _) in PRODUCT_TYPES.get(product.get('category'), {}).items():
        prefix = prefix.casefold()
        if name == prefix or name.startswith(prefix + ' '):
            return label
    return 'Khác'


def demo_product_details(product):
    """Clean up the original demo records and derive facts from their names."""
    category = product.get('category')
    name = product.get('name') or ''
    product_type = infer_product_type(product)
    entry = PRODUCT_TYPES.get(category, {}).get(product_type)
    if not entry or product.get('product_type'):
        return {}
    prefix, fields = entry
    if not re.fullmatch(re.escape(prefix) + r' (?:Gen |Pro |V)\d+', name, re.IGNORECASE):
        return {}

    original = product.get('attributes') or {}
    attributes = {key: value for key, value in original.items()
                  if (key in fields or key not in FIELDS) and value != 'Không áp dụng'}
    if product_type in ('Điện thoại', 'Laptop'):
        # The original seed assigned desktop processors to phones and Apple CPUs to Dell.
        if product_type == 'Điện thoại' or 'apple' in str(attributes.get('cpu', '')).casefold():
            attributes.pop('cpu', None)
    if product_type == 'Giày sneaker':
        sizes = attributes.get('size')
        if isinstance(sizes, list) and sizes and all(size in ('S', 'M', 'L', 'XL', 'FreeSize') for size in sizes):
            attributes.pop('size')
    for brand in ('Dell', 'Samsung', 'LG', 'JBL'):
        if brand.casefold() in prefix.casefold().split():
            attributes['brand'] = brand
    if product_type == 'Ổ cứng SSD':
        attributes['storage'] = '1 TB'
    if product_type == 'Bộ nồi':
        attributes.setdefault('material', 'Inox')
    if 'Bluetooth' in prefix:
        attributes['connection'] = 'Bluetooth'

    details = {'product_type': product_type, 'attributes': attributes}
    if not (product.get('description') or '').strip():
        details['description'] = f'{name} thuộc nhóm {product_type.lower()} trong danh mục {category.lower()}.'
    return details
