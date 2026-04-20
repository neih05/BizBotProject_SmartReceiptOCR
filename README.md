# 🧾 BizBot — Bot Telegram trích xuất hóa đơn

Bot tự động đọc ảnh hóa đơn, trích xuất thông tin bằng Gemini AI và lưu vào database.

---

## 📁 Cấu trúc project

```
bizbot/
├── bot.py              # File chính, chạy bot
├── gemini_handler.py   # Gọi Gemini Vision API
├── database.py         # SQLite — lưu & truy vấn hóa đơn
├── formatter.py        # Format kết quả đẹp để reply
├── requirements.txt    # Thư viện cần cài
├── .env                # Token & API key (KHÔNG commit lên GitHub)
└── .env.example        # Mẫu file .env
```

---

## ⚙️ Hướng dẫn cài đặt & chạy

### Bước 1 — Lấy Token Telegram

1. Mở Telegram, tìm **@BotFather**
2. Gõ `/newbot` → đặt tên → lấy token dạng `123456:AAFxxx...`

### Bước 2 — Lấy Gemini API Key

1. Vào [https://aistudio.google.com](https://aistudio.google.com)
2. Đăng nhập Google → bấm **Get API Key** → **Create API key**
3. Copy key dạng `AIzaSyxxx...`

### Bước 3 — Tạo file .env

Tạo file `.env` trong thư mục project (copy từ `.env.example`):

```
TELEGRAM_TOKEN=your_telegram_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Bước 4 — Cài thư viện

```bash
pip install -r requirements.txt
```

### Bước 5 — Chạy bot

```bash
python bot.py
```

Nếu thấy log `BizBot đang chạy...` là thành công ✅

---

## 🤖 Các lệnh bot hỗ trợ

| Lệnh | Mô tả |
|------|-------|
| `/start` | Chào mừng & hướng dẫn |
| `/help` | Xem hướng dẫn sử dụng |
| `/history` | Xem 5 hóa đơn gần nhất |
| Gửi ảnh | Phân tích & lưu hóa đơn |

---

## 🗃️ Cấu trúc database

File `invoices.db` (SQLite) tự động tạo khi chạy lần đầu.

Bảng `invoices`:

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER | Mã hóa đơn tự tăng |
| user_id | INTEGER | ID người dùng Telegram |
| store_name | TEXT | Tên cửa hàng |
| date | TEXT | Ngày trên hóa đơn |
| items | TEXT | JSON danh sách hàng |
| total_amount | REAL | Tổng tiền |
| raw_json | TEXT | Toàn bộ JSON từ Gemini |
| created_at | TEXT | Thời gian lưu |

---

## ⚠️ Lưu ý

- File `.env` chứa thông tin nhạy cảm — **KHÔNG** đưa lên GitHub
- Thêm `.env` vào `.gitignore`
- Gemini free tier: ~1500 request/ngày, đủ để demo
- Ảnh hóa đơn cần rõ nét, đủ sáng để AI đọc chính xác
