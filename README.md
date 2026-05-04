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
bizbot/
├── bot.py              # File chính, chạy bot Telegram
├── gemini_handler.py   # Gọi Gemini Vision API để phân tích ảnh hóa đơn
├── database.py         # Quản lý SQLite — lưu & truy vấn hóa đơn, người dùng
├── formatter.py        # Format kết quả đẹp để reply trên Telegram
├── api.py              # FastAPI Backend cung cấp API cho Dashboard
├── dashboard/          # React Vite Web Dashboard cho Kế toán
├── requirements.txt    # Thư viện Python cần cài
├── .env                # Token & API key (KHÔNG commit lên GitHub)
└── .env.example        # Mẫu file .env
```

---

## 💻 Yêu cầu hệ thống (Prerequisites)
- **Python 3.9+**
- **Node.js 18+** & **npm** (để chạy Web Dashboard)
- Tài khoản Telegram (để tạo bot) và [Google AI Studio](https://aistudio.google.com) (để lấy Gemini API Key)

---

## ⚙️ Hướng dẫn cài đặt & chạy

### Bước 1 — Lấy API Keys
1. **Telegram Bot Token**: Vào Telegram, tìm **@BotFather**, gõ `/newbot` và làm theo hướng dẫn để lấy token.
2. **Gemini API Key**: Vào Google AI Studio, tạo một API Key miễn phí.

### Bước 2 — Cấu hình biến môi trường
Tạo file `.env` ở thư mục gốc (copy từ `.env.example`):
```env
TELEGRAM_TOKEN=your_telegram_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Bước 3 — Cài đặt và chạy hệ thống

Hệ thống gồm 3 thành phần chạy song song. Vui lòng mở 3 cửa sổ Terminal (Command Prompt) riêng biệt:

#### 1. Chạy Telegram Bot (Xử lý hóa đơn)
```bash
pip install -r requirements.txt
python bot.py
```
*(Nếu thấy log `BizBot đang chạy...` là thành công)*

#### 2. Chạy Backend API (Cung cấp API cho web)
Mở một terminal mới và chạy:
```bash
# Nếu dùng Windows:
.venv\Scripts\python -m uvicorn api:app --reload

# Nếu dùng Mac/Linux:
.venv/bin/python -m uvicorn api:app --reload
```
*(Backend sẽ chạy tại http://localhost:8000)*

#### 3. Chạy Web Dashboard (Dành cho Kế toán)
Mở một terminal mới, chuyển vào thư mục `dashboard`:
```bash
cd dashboard
npm install
npm run dev
```
*(Dashboard sẽ chạy tại http://localhost:5173)*

---

## 🔐 Thông tin đăng nhập Web Dashboard

Sau khi Backend và Web Dashboard đã chạy thành công, hãy mở trình duyệt và truy cập vào địa chỉ: **http://localhost:5173**

Sử dụng tài khoản Kế toán / Admin mặc định để đăng nhập:
- **Tên đăng nhập:** `admin`
- **Mật khẩu:** `admin`

---

## 🤖 Các lệnh Bot Telegram

| Lệnh | Mô tả |
|------|-------|
| `/start` | Khởi động bot & tự động đăng ký hệ thống |
| `/help` | Xem hướng dẫn sử dụng chi tiết |
| `/history` | Xem 5 hóa đơn gần nhất của bạn |
| `/expense` | Nhập chi phí thủ công (VD: `/expense 50000 An trua`) |
| Gửi ảnh | AI sẽ tự động phân tích, kiểm tra trùng lặp & lưu hóa đơn |

---

## 🗃️ Cấu trúc hệ thống & Database

Dữ liệu được lưu trong file `invoices.db` (SQLite) và tự động tạo khi chạy lần đầu. 
> **Mẹo:** Để **reset toàn bộ dữ liệu** (xóa hết hóa đơn, người dùng để demo lại từ đầu), bạn chỉ cần tắt bot, xóa file `invoices.db` rồi chạy lại bot.

Hệ thống kết nối chặt chẽ giữa 3 thành phần:
1. **Bot Telegram**: Người dùng gửi ảnh, Bot dùng AI phân tích, cảnh báo trùng lặp (nếu có), lưu vào DB và báo cho Kế toán (trên Dashboard).
2. **Web Dashboard**: Giao diện UI cho kế toán xem báo cáo, quản lý nhân viên, và duyệt/từ chối hóa đơn.
3. **Backend API**: Khi kế toán thao tác trên web, API sẽ lưu trạng thái vào DB và tự động gửi tin nhắn Telegram báo kết quả lại cho người dùng thông qua Bot.

---

## ⚠️ Lưu ý

- File `.env` chứa thông tin nhạy cảm — **KHÔNG** đưa lên GitHub. Thêm vào `.gitignore`.
- Gemini free tier có giới hạn request nhất định nhưng đủ dùng cho quy mô nhỏ & demo.

