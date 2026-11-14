# E-commerce NoSQL — Flask + MongoDB

Khung project ban đầu cho đề tài sàn thương mại điện tử đa ngành hàng.

## Yêu cầu
- Python 3.10+
- Quyền truy cập MongoDB Atlas (cluster `Cluster0` cho bản demo hiện tại)
- MongoDB Compass (khuyến nghị để kiểm tra dữ liệu)

## Cài đặt trên Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Mở `.env` và đổi `FLASK_SECRET_KEY` thành chuỗi ngẫu nhiên dài trước khi sử dụng nghiêm túc.

## Kết nối dữ liệu MongoDB Atlas

1. Trong MongoDB Atlas, mở project chứa `Cluster0`. Thêm IP của máy chạy Flask vào **IP Access List**. Trong **Database Access**, dùng một **Database User** có quyền đọc và ghi database `ecommerce_demo_bao_ve`.
2. Tại `Cluster0`, chọn **Connect → Drivers and Client Libraries → Python** và sao chép chuỗi kết nối. Thay phần giữ chỗ bằng tài khoản Database User. Mã hóa URL các ký tự đặc biệt trong tên người dùng hoặc mật khẩu nếu có, ví dụ `@` thành `%40`.
3. Trong file `.env` ở thư mục dự án, đặt hai biến sau bằng thông tin của cluster:

```dotenv
MONGO_URI=mongodb+srv://<db-user>:<db-password>@<atlas-host>/?retryWrites=true&w=majority
MONGO_DB=ecommerce_demo_bao_ve
```

Flask và các lệnh trong `scripts` đọc `MONGO_URI` để kết nối và `MONGO_DB` để chọn database. Nếu đã lưu chuỗi Atlas dưới `ATLAS_URI`, hãy dùng chuỗi đó làm giá trị của `MONGO_URI`. Biến môi trường đã đặt trong PowerShell được ưu tiên hơn `.env`. Khởi động lại Flask sau khi sửa cấu hình.

Database demo hiện tại đã có dữ liệu và index. Để kiểm tra, mở **Cluster0 → Browse Collections → ecommerce_demo_bao_ve**. Bạn sẽ thấy các collection `sanpham`, `danhmuc`, `users`, `reviews` và `hoadon`. [Hướng dẫn kết nối Atlas](https://www.mongodb.com/docs/atlas/connect-to-database-deployment/)

## Chạy ứng dụng

```powershell
python app.py
```

- Trang chủ tại http://127.0.0.1:5000/
- Kiểm tra MongoDB tại http://127.0.0.1:5000/health. Kết nối thành công trả HTTP 200.
- Cửa hàng tại http://127.0.0.1:5000/products
- Quản trị tại http://127.0.0.1:5000/admin/dashboard

## Tạo database demo mới (tùy chọn)

Chỉ thực hiện phần này khi cần bộ dữ liệu riêng. Đặt `MONGO_DB` thành tên database trống và bảo đảm Database User có quyền trên database đó. Ví dụ cho phiên PowerShell hiện tại:

```powershell
$env:MONGO_DB = "ecommerce_demo_thu_nghiem"
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
