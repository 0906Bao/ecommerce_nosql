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

Mở:
- Website: http://127.0.0.1:5000
- Kiểm tra kết nối: http://127.0.0.1:5000/health
- Danh sách sản phẩm: http://127.0.0.1:5000/products/
- Dashboard khung: http://127.0.0.1:5000/admin/

## Lưu ý
- Đây mới là khung project, chưa triển khai CRUD đầy đủ, xác thực, phân quyền, giỏ hàng, đặt hàng hay Aggregation Pipeline.
- Không đưa `.env` thật lên Git.
- Dashboard hiện chưa hiển thị số liệu thật.
- Các route quản trị hiện chưa được bảo vệ; phải bổ sung xác thực và kiểm tra vai trò trước khi demo hoặc triển khai.
