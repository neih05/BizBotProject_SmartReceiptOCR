import os
import logging
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from database import init_db, save_invoice, get_history, count_user_invoices, is_duplicate
from gemini_handler import setup_gemini, extract_invoice
from formatter import format_invoice, format_history
from datetime import datetime

# ── Load biến môi trường ──────────────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Thiếu TELEGRAM_TOKEN hoặc GEMINI_API_KEY trong file .env")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Khởi tạo Gemini ───────────────────────────────────────────────────────────
setup_gemini(GEMINI_API_KEY)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start — chào người dùng."""
    await update.message.reply_text(
        "👋 Xin chào! Tôi là *BizBot* — bot trích xuất hóa đơn tự động.\n\n"
        "📸 Gửi ảnh hóa đơn cho tôi, tôi sẽ đọc và lưu thông tin giúp bạn.\n\n"
        "📋 Dùng /history để xem 5 hóa đơn gần nhất.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /help."""
    await update.message.reply_text(
        "*Hướng dẫn sử dụng BizBot:*\n\n"
        "1️⃣ Chụp hoặc chọn ảnh hóa đơn\n"
        "2️⃣ Gửi ảnh vào chat này\n"
        "3️⃣ Đợi vài giây để bot xử lý\n"
        "4️⃣ Nhận kết quả trích xuất\n\n"
        "/history — xem 5 hóa đơn gần nhất\n"
        "/help    — xem hướng dẫn này",
        parse_mode="Markdown",
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /history — xem lịch sử hóa đơn."""
    user_id = update.effective_user.id
    rows = get_history(user_id, limit=5)
    text = format_history(rows)
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý ảnh hóa đơn được gửi lên."""
    user_id   = update.effective_user.id
    user_name = update.effective_user.first_name or "bạn"

    # Thông báo đang xử lý
    processing_msg = await update.message.reply_text(
        "⏳ Đang phân tích hóa đơn, vui lòng chờ..."
    )

    try:
        # 1. Download ảnh chất lượng cao nhất
        photo = update.message.photo[-1]
        file  = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        logger.info(f"[User {user_id}] Nhận ảnh {photo.file_id}, size={len(image_bytes)} bytes")

        # 2. Gửi lên Gemini để trích xuất
        data = extract_invoice(bytes(image_bytes))
        logger.info(f"[User {user_id}] Gemini trả về: {data}")

        if data.get("is_invoice") is False:
            await processing_msg.edit_text("⚠️ Đây không phải hóa đơn, vui lòng gửi lại ảnh khác.")
            return

        store_name = data.get("store_name", "Không rõ")
        date_str = data.get("date", "Không rõ")
        total_amount = data.get("total_amount", 0)

        is_dup = is_duplicate(user_id, store_name, date_str, total_amount)

        # 3. Format kết quả đẹp và gửi kèm nút xác nhận
        result_text = format_invoice(data)
        if is_dup:
            result_text += "\n\n⚠️ Cảnh báo: Hóa đơn này có dấu hiệu trùng lặp với dữ liệu đã có!"

        context.user_data['temp_invoice'] = data

        keyboard = [
            [
                InlineKeyboardButton("Xác nhận ✅", callback_data="confirm_invoice"),
                InlineKeyboardButton("Sửa thủ công ✏️", callback_data="edit_invoice")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await processing_msg.delete()
        await update.message.reply_text(result_text, parse_mode="Markdown", reply_markup=reply_markup)

    except ValueError as e:
        # Gemini trả về JSON không hợp lệ
        logger.warning(f"[User {user_id}] Lỗi parse JSON: {e}")
        await processing_msg.edit_text(
            "⚠️ Bot không đọc được thông tin từ ảnh này.\n"
            "Hãy thử lại với ảnh rõ hơn, đủ sáng và không bị mờ."
        )

    except Exception as e:
        logger.error(f"[User {user_id}] Lỗi không xác định: {e}", exc_info=True)
        await processing_msg.edit_text(
            "❌ Đã xảy ra lỗi trong quá trình xử lý.\n"
            "Vui lòng thử lại sau ít phút."
        )


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhắc user khi gửi tin nhắn không phải ảnh."""
    await update.message.reply_text(
        "📸 Vui lòng gửi *ảnh* hóa đơn để tôi xử lý.\n"
        "Dùng /help để xem hướng dẫn.",
        parse_mode="Markdown",
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if query.data == "confirm_invoice":
        data = context.user_data.get('temp_invoice')
        if not data:
            await query.edit_message_text("❌ Không tìm thấy dữ liệu hóa đơn tạm thời. Vui lòng gửi lại ảnh.")
            return

        invoice_id = save_invoice(user_id, data)
        count = count_user_invoices(user_id)

        result_text = format_invoice(data)
        result_text += f"\n\n✅ *Đã lưu* — Mã hóa đơn: #{invoice_id} (Hóa đơn thứ {count} của bạn)"

        await query.edit_message_text(result_text, parse_mode="Markdown")
        context.user_data.pop('temp_invoice', None)

    elif query.data == "edit_invoice":
        await query.edit_message_text(
            query.message.text + "\n\n" +
            "Nếu AI đọc sai, bạn hãy dùng lệnh:\n"
            "`/chi [Số tiền] [Tên_cửa_hàng]`\n"
            "Ví dụ: `/chi 150000 Highland Coffee`\n"
            "để nhập thủ công nhé!",
            parse_mode="Markdown"
        )
        context.user_data.pop('temp_invoice', None)

async def cmd_chi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /chi [Số tiền] [Tên_cửa_hàng]"""
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text("Vui lòng dùng đúng cú pháp:\n`/chi [Số tiền] [Tên_cửa_hàng]`\nVí dụ: `/chi 150000 Highland Coffee`", parse_mode="Markdown")
        return

    try:
        amount_str = args[0].replace(',', '').replace('.', '')
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Số tiền không hợp lệ.")
        return

    store_name = " ".join(args[1:])
    today_str = datetime.now().strftime("%d/%m/%Y")

    data = {
        "is_invoice": True,
        "store_name": store_name,
        "date": today_str,
        "items": [],
        "total_amount": amount
    }

    invoice_id = save_invoice(user_id, data)
    count = count_user_invoices(user_id)

    await update.message.reply_text(
        f"✅ *Đã lưu hóa đơn thủ công*\n"
        f"Mã hóa đơn: #{invoice_id} (Hóa đơn thứ {count} của bạn)\n"
        f"Cửa hàng: {store_name}\n"
        f"Số tiền: {amount:,.0f}đ",
        parse_mode="Markdown"
    )


# ── Khởi chạy bot ─────────────────────────────────────────────────────────────

def main():
    init_db()
    logger.info("Database đã sẵn sàng.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("chi",     cmd_chi))
    app.add_handler(MessageHandler(filters.PHOTO,                   handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("BizBot đang chạy... Bấm Ctrl+C để dừng.")
    app.run_polling()


if __name__ == "__main__":
    main()
