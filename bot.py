import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from database import init_db, save_invoice, get_history
from gemini_handler import setup_gemini, extract_invoice
from formatter import format_invoice, format_history

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

        # 3. Lưu vào database
        invoice_id = save_invoice(user_id, data)
        logger.info(f"[User {user_id}] Đã lưu invoice #{invoice_id}")

        # 4. Format kết quả đẹp và reply
        result_text = format_invoice(data)
        result_text += f"\n\n✅ *Đã lưu* — Mã hóa đơn: #{invoice_id}"

        await processing_msg.delete()
        await update.message.reply_text(result_text, parse_mode="Markdown")

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


# ── Khởi chạy bot ─────────────────────────────────────────────────────────────

def main():
    init_db()
    logger.info("Database đã sẵn sàng.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(MessageHandler(filters.PHOTO,                   handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo))

    logger.info("BizBot đang chạy... Bấm Ctrl+C để dừng.")
    app.run_polling()


if __name__ == "__main__":
    main()
