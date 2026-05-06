# 🧾 BizBot — Hệ Thống Quản Lý & Trích Xuất Hóa Đơn Thông Minh

Hệ thống bao gồm một Bot Telegram tự động đọc ảnh hóa đơn, trích xuất thông tin bằng Gemini AI, một Backend API và một Web Dashboard dành cho kế toán quản lý và duyệt hóa đơn.

---

## ✨ Tính năng nổi bật

1. **Bot Telegram Thông Minh**: Người dùng gửi ảnh hóa đơn, bot tự động dùng AI (Gemini Vision) để đọc và trích xuất thông tin (Số tiền, ngày tháng, tên cửa hàng).
2. **Kiểm tra trùng lặp (Duplicate Detection)**: Tự động cảnh báo và ngăn chặn gửi trùng hóa đơn dựa trên số tiền, ngày và tên cửa hàng.
3. **Web Dashboard Quản Trị**: Giao diện trực quan dành cho Kế toán để theo dõi, duyệt/từ chối hóa đơn, và xem báo cáo thống kê.
4. **Quy trình duyệt (Approval Workflow)**: Hóa đơn được giữ ở trạng thái "Chờ duyệt", kế toán thao tác trên web và bot sẽ tự động nhắn tin phản hồi kết quả cho người dùng.

---

## 📁 Cấu trúc project

```
BizBot_NopBai/
├── bot.py              # File chính, chạy bot Telegram
├── gemini_handler.py   # Gọi Gemini Vision API để phân tích ảnh hóa đơn
├── database.py         # Quản lý SQLite — lưu & truy vấn hóa đơn, người dùng
├── formatter.py        # Format kết quả đẹp để reply trên Telegram
├── api.py              # FastAPI Backend cung cấp API cho Dashboard
├── dashboard/          # React Vite Web Dashboard cho Kế toán
├── requirements.txt    # Thư viện Python cần cài
├── .env                # Token & API key
└── .env.example        # Mẫu file .env
```

---

## 💻 Yêu cầu hệ thống

- **Python 3.9+** (khuyến nghị 3.11)
- **Node.js 18+** & **npm** (để chạy Web Dashboard)
- Kết nối Internet (để bot giao tiếp với Telegram API và Gemini AI)

---

## ⚙️ Hướng dẫn cài đặt & chạy (từ file ZIP)

### Bước 1 — Giải nén và chuẩn bị

1. Giải nén file ZIP vào một thư mục bất kỳ.
2. Mở **Command Prompt** hoặc **PowerShell** và `cd` vào thư mục vừa giải nén.

### Bước 2 — Cấu hình biến môi trường

Mở file `.env` trong thư mục gốc và điền API Key:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Cách lấy Token:**
> - **Telegram Bot Token**: Vào Telegram, tìm **@BotFather**, gõ `/newbot` và làm theo hướng dẫn.
> - **Gemini API Key**: Vào [Google AI Studio](https://aistudio.google.com), tạo một API Key miễn phí.

### Bước 3 — Khởi tạo Môi trường ảo (Khuyên dùng)

Để tránh xung đột thư viện trên máy tính, vui lòng khởi tạo môi trường ảo mới:

```PowerShell
# 1. Tạo môi trường ảo
python -m venv venv

# 2. Kích hoạt môi trường (Windows)
.\venv\Scripts\activate

# 2. Kích hoạt môi trường (Mac/Linux)
source venv/bin/activate

### Bước 4 — Cài đặt thư viện Python

```bash
pip install --upgrade pip
pip install --only-binary :all: -r requirements.txt
pip install -r requirements.txt


### Bước 4 — Chạy hệ thống (cần 3 cửa sổ Terminal)

Hệ thống gồm **3 thành phần** chạy song song. Mở **3 cửa sổ Terminal** riêng biệt và chạy từng lệnh:

#### Terminal 1 — Chạy Telegram Bot
```bash
python bot.py
```
✅ Thành công khi thấy: `BizBot đang chạy... Bấm Ctrl+C để dừng.`

#### Terminal 2 — Chạy Backend API
```bash
# Windows:
python -m uvicorn api:app --reload

# Mac/Linux:
python3 -m uvicorn api:app --reload
```
✅ Thành công khi thấy: `Uvicorn running on http://127.0.0.1:8000`

#### Terminal 3 — Chạy Web Dashboard
```bash
cd dashboard
npm install
npm run dev
```
✅ Thành công khi thấy: `Local: http://localhost:5173/`

---

## 🔐 Đăng nhập Web Dashboard

Sau khi cả 3 thành phần đã chạy, mở trình duyệt và truy cập:

👉 **http://localhost:5173**

Sử dụng tài khoản mặc định:

| Thông tin | Giá trị |
|-----------|---------|
| **Username** | `admin` |
| **Password** | `admin` |

---

## 🤖 Thông tin Bot Telegram

Username Bot: @bizbot_receipt_bot

| Lệnh | Mô tả |
|------|-------|
| `/start` | Khởi động bot & tự động đăng ký hệ thống |
| `/help` | Xem hướng dẫn sử dụng chi tiết |
| `/history` | Xem 5 hóa đơn gần nhất của bạn |
| `/expense` | Nhập chi phí thủ công (VD: `/expense 50000 An trua`) |
| Gửi ảnh | AI sẽ tự động phân tích, kiểm tra trùng lặp & lưu hóa đơn |

> **Lưu ý:** Nhân viên cần được thêm Telegram ID vào hệ thống (qua Dashboard > Quản lý Nhân viên) trước khi có thể sử dụng bot.

---

## 🗃️ Database

- Dữ liệu được lưu trong file `invoices.db` (SQLite), tự động tạo khi chạy lần đầu.
- Tài khoản đăng nhập web `admin/admin` cũng được tự động tạo khi khởi động.
- **Để reset toàn bộ dữ liệu**: Tắt bot, xóa file `invoices.db`, rồi chạy lại.

---

## 🔄 Luồng hoạt động

1. **Nhân viên** gửi ảnh hóa đơn qua **Bot Telegram**.
2. **Bot** dùng **Gemini AI** phân tích ảnh → trích xuất thông tin → kiểm tra trùng lặp → lưu vào DB (trạng thái: *Chờ duyệt*).
3. **Kế toán** đăng nhập **Web Dashboard** → xem danh sách hóa đơn → duyệt hoặc từ chối.
4. Khi kế toán thao tác trên web, **API** tự động gửi tin nhắn Telegram thông báo kết quả cho nhân viên.

---

## ⚠️ Lưu ý

- File `.env` chứa thông tin nhạy cảm (token, API key).
- Lỗi ModuleNotFoundError: Đảm bảo đã chạy lệnh kích hoạt môi trường ảo (activate) ở mỗi Terminal chạy Python.
- Gemini free tier có giới hạn request nhưng đủ dùng cho demo.
- Nếu bot báo lỗi `ConnectError`, hãy kiểm tra kết nối mạng và thử chạy lại.

