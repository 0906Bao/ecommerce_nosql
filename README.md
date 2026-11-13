# E-commerce NoSQL — Flask + MongoDB

Khung project ban đầu cho đề tài sàn thương mại điện tử đa ngành hàng.

## Yêu cầu
- Python 3.10+
- MongoDB đang chạy cục bộ hoặc MongoDB Atlas
- MongoDB Compass (khuyến nghị để kiểm tra dữ liệu)

## Cài đặt trên Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `.env` và đổi `FLASK_SECRET_KEY` thành chuỗi ngẫu nhiên dài trước khi sử dụng nghiêm túc.

## Khởi tạo index

```powershell
python -m scripts.init_db
```

Lệnh này kiểm tra kết nối MongoDB và tạo các index cơ bản. MongoDB phải đang chạy.

## Chạy ứng dụng

```powershell
python app.py
```

- Trang chủ tại http://127.0.0.1:5000/
- Kiểm tra MongoDB tại http://127.0.0.1:5000/health. Kết nối thành công trả HTTP 200.
- Cửa hàng tại http://127.0.0.1:5000/products
- Quản trị tại http://127.0.0.1:5000/admin/dashboard

## Chuẩn bị database demo

Khởi động MongoDB và kiểm tra `MONGO_URI` trong `.env`. Trong PowerShell, chọn tên database demo mới rồi chạy:

```powershell
$env:MONGO_DB = "ecommerce_demo_bao_ve"
python -m scripts.init_db
python -m scripts.seed_data --db $env:MONGO_DB --products 100 --orders 50
python app.py
```

Các số trên là mặc định của project. Đổi tham số theo định mức chính thức khi có. Seed tạo ba danh mục và từ hai đến năm mặt hàng mỗi đơn. Chọn tên database mới khi cần seed lại.

Seed tạo 3–10 đánh giá mẫu cho mỗi sản phẩm mới. Để bổ sung đánh giá cho sản phẩm đã có trong database demo, chạy:

```powershell
python -m scripts.seed_data --db $env:MONGO_DB --reviews-only
```

Lệnh này bổ sung cho sản phẩm có dưới 3 đánh giá và giữ các đánh giá đã có.

## Chạy thử demo

1. Mở `/health` và kiểm tra HTTP 200. Đăng nhập bằng tài khoản demo `admin` / `123456`.
2. Mở `/categories/manage`. Tạo danh mục, đổi tên khi danh mục còn trống, rồi tạo sản phẩm thuộc danh mục đó ở `/admin/products`.
3. Mở cửa hàng, thêm sản phẩm vào giỏ và đặt hàng. Kiểm tra `hoadon.items.price_at_purchase` trong MongoDB Compass.
4. Sửa giá sản phẩm và kiểm tra lại hóa đơn vừa tạo. Đơn giá và thành tiền trên hóa đơn phải giữ nguyên. Xóa sản phẩm, sau đó xóa danh mục.
5. Mở dashboard, chọn khoảng ngày và thử nhóm theo ngày hoặc tháng. Kiểm tra số đơn, doanh thu và Top 5 trong cùng khoảng. Dashboard dùng múi giờ Việt Nam và tính tổng giá trị đơn đã tạo.

Không đưa `.env` thật lên Git. Tài khoản quản trị mặc định chỉ dùng cho demo cục bộ.
