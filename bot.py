import os
import logging
import csv
from dotenv import load_dotenv
import json

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from database import (
    init_db, save_invoice, get_history, count_user_invoices, is_duplicate,
    get_user, save_user, update_user_status, get_pending_invoices,
    update_invoice_status, get_approved_invoices_for_report, get_users_with_stats,
    get_all_invoices_for_export, get_daily_report, get_employee_by_nickname, get_employee_by_id
)
from gemini_handler import setup_gemini, extract_invoice
from formatter import format_invoice, format_history
from datetime import datetime
from telegram import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

# ── Load biến môi trường ──────────────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY or not ADMIN_ID:
    raise ValueError("Thiếu TELEGRAM_TOKEN, GEMINI_API_KEY hoặc ADMIN_ID trong file .env")

ADMIN_ID = int(ADMIN_ID)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Khởi tạo Gemini ───────────────────────────────────────────────────────────
setup_gemini(GEMINI_API_KEY)


# ── States cho ConversationHandler ────────────────────────────────────────────
WAIT_PHOTO_CONFIRM = 3
WAIT_PHOTO_EDIT = 4

# ── Middleware kiểm tra User ──────────────────────────────────────────────────
async def check_user_verified(update: Update) -> bool:
    user_id = update.effective_user.id
    
    # Check against employees table using telegram_id (stored in employee_id)
    emp = get_employee_by_id(str(user_id))
    if not emp:
        await update.message.reply_text(
            f"⛔ *Truy cập bị từ chối*\n"
            f"Bạn chưa được cấp quyền truy cập hệ thống.\n"
            f"Vui lòng gửi mã ID này cho Kế toán để được thêm vào danh sách nhân viên:\n"
            f"`{user_id}`",
            parse_mode="Markdown"
        )
        return False

    user = get_user(user_id)
    if not user:
        # Use real name from employees table
        save_user(user_id, emp["real_name"], "DEFAULT_COMPANY", "staff", True)
    return True

# ── Handlers Chào Mừng & Xác Thực ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start."""
    user_id = update.effective_user.id
    name = update.effective_user.full_name or "Unknown"
    
    user = get_user(user_id)
    if not user:
        save_user(user_id, name, "DEFAULT_COMPANY", "staff", True)

    await update.message.reply_text(
        f"👋 Xin chào {name}!\n\n"
        "📸 Bạn có thể gửi ảnh hóa đơn cho tôi để đưa vào danh sách chờ duyệt.\n"
        "📋 Dùng /history để xem 5 hóa đơn gần nhất.\n"
        "✏️ Dùng /expense [số tiền] [Tên_cửa_hàng] để nhập tay.\n"
        "Ví dụ: `/expense 50000 Cơm trưa văn phòng`",
        parse_mode="Markdown"
    )



# ── Nghiệp vụ Hóa Đơn ────────────────────────────────────────────────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return ConversationHandler.END
        
    user_id   = update.effective_user.id

    processing_msg = await update.message.reply_text("⏳ Đang phân tích hóa đơn, vui lòng chờ...")

    try:
        photo = update.message.photo[-1]
        file  = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        data = extract_invoice(bytes(image_bytes))

        if data.get("is_invoice") is False:
            await processing_msg.edit_text("⚠️ Đây không phải hóa đơn, vui lòng gửi lại ảnh khác.")
            return ConversationHandler.END

        # Lưu thông tin tạm
        data['file_id'] = photo.file_id
        context.user_data['temp_invoice'] = data

        # Check trùng
        store = data.get("store_name", "")
        date = data.get("date", "")
        amt = data.get("total_amount", 0)
        
        is_dup = False
        if store and date and amt:
            is_dup = is_duplicate(store, date, amt)
            data['is_suspicious_duplicate'] = is_dup

        result_text = format_invoice(data)
        category_str = data.get("category") or "Khác"
        
        if is_dup:
            result_text = "⚠️ *CẢNH BÁO TRÙNG LẶP*\nHệ thống phát hiện hóa đơn này (cùng cửa hàng, cùng ngày, cùng số tiền) có vẻ đã được gửi trước đó. Kế toán sẽ kiểm tra kỹ hóa đơn này!\n\n" + result_text
            keyboard = [
                [
                    InlineKeyboardButton("✅ Dù trùng nhưng vẫn lưu", callback_data="confirm_correct"),
                    InlineKeyboardButton("✏️ Chỉnh sửa", callback_data="edit_invoice")
                ]
            ]
        else:
            result_text += f"\n\nDanh mục dự đoán: {category_str}. Xác nhận?"
            keyboard = [
                [
                    InlineKeyboardButton("✅ Xác nhận đúng", callback_data="confirm_correct"),
                    InlineKeyboardButton("✏️ Chỉnh sửa", callback_data="edit_invoice")
                ]
            ]
        
        await processing_msg.edit_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return WAIT_PHOTO_CONFIRM

    except ValueError as e:
        logger.warning(f"Lỗi parse JSON: {e}")
        await processing_msg.edit_text("⚠️ Bot không đọc được thông tin. Hãy thử ảnh rõ hơn.")
        return ConversationHandler.END
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Lỗi không xác định: {error_msg}", exc_info=True)
        if "429" in error_msg or "quota" in error_msg.lower():
            await processing_msg.edit_text("⏳ Hệ thống AI đang bị quá tải (vượt số lượt cho phép). Vui lòng đợi khoảng 1 phút rồi gửi lại ảnh bạn nhé.")
        else:
            await processing_msg.edit_text("❌ Đã xảy ra lỗi hệ thống khi đọc ảnh.")
        return ConversationHandler.END

async def photo_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_data = context.user_data.get('temp_invoice')
    user_id = update.effective_user.id
    
    if not user_data:
        await query.edit_message_text("❌ Phiên làm việc đã hết hạn. Vui lòng gửi lại ảnh hóa đơn.")
        return ConversationHandler.END
        
    if data == "confirm_correct":
        is_dup = user_data.get('is_suspicious_duplicate', False)
        invoice_id = save_invoice(user_id, user_data, status='pending')
        await query.edit_message_text(f"{query.message.text}\n\n✅ *Đã lưu thành công!*\n(Mã hóa đơn chờ duyệt: #{invoice_id})", parse_mode="Markdown")
        
        if is_dup:
            # Alert Admin
            store = user_data.get("store_name", "Không rõ")
            amount = user_data.get("total_amount", 0)
            user_info = get_user(user_id)
            user_name = user_info['full_name'] if user_info else f"ID: {user_id}"
            
            admin_msg = (
                f"🚨 *CẢNH BÁO TRÙNG LẶP HÓA ĐƠN*\n\n"
                f"Nhân viên: {user_name}\n"
                f"Cửa hàng: {store}\n"
                f"Số tiền: {amount:,.0f} đ\n"
                f"Mã draft: #{invoice_id}\n\n"
                f"Vui lòng vào Dashboard (Web) để xem xét và duyệt."
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Cannot send warning to admin: {e}")
                
        context.user_data.pop('temp_invoice', None)
        return ConversationHandler.END
        
    elif data == "edit_invoice":
        await query.edit_message_text(
            f"{query.message.text}\n\nBạn hãy gõ lại thông tin theo cú pháp sau:\n"
            "`/expense [Số tiền] [Tên cửa hàng]`\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng`",
            parse_mode="Markdown"
        )
        return WAIT_PHOTO_EDIT

async def photo_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data.get('temp_invoice')
    user_id = update.effective_user.id
    
    if not user_data:
        await update.message.reply_text("❌ Phiên làm việc đã hết hạn. Vui lòng gửi lại ảnh hóa đơn.")
        return ConversationHandler.END
        
    if text.startswith("/expense "):
        raw_args = text[9:].strip()
        args = raw_args.split()
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Cú pháp không hợp lệ. Vui lòng gõ lại theo định dạng:\n"
                "`/expense [Số tiền] [Tên_cửa_hàng]`\n"
                "Ví dụ: `/expense 50000 Cơm trưa văn phòng`",
                parse_mode="Markdown"
            )
            return WAIT_PHOTO_EDIT
            
        amount_str = args[0]
        store_name = " ".join(args[1:]) if len(args) > 1 else user_data.get("store_name", "Không rõ")
        category = user_data.get("category", "Không phân loại")
    else:
        amount_str = text
        store_name = user_data.get("store_name", "Không rõ")
        category = user_data.get("category", "Khác")
        
    try:
        amount_str = amount_str.replace(',', '').replace('.', '')
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("❌ Số tiền không hợp lệ. Vui lòng gõ lại số tiền chính xác:")
        return WAIT_PHOTO_EDIT
        
    user_data["total_amount"] = amount
    user_data["store_name"] = store_name
    user_data["category"] = category
    
    invoice_id = save_invoice(user_id, user_data, status='pending')
    
    await update.message.reply_text(
        f"✅ *Đã lưu thành công bản cập nhật!*\n"
        f"Mã hóa đơn chờ duyệt: #{invoice_id}\nCửa hàng: {store_name}\nSố tiền mới: {amount:,.0f} đ",
        parse_mode="Markdown"
    )
    context.user_data.pop('temp_invoice', None)
    return ConversationHandler.END

async def cancel_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('temp_invoice', None)
    await update.message.reply_text("Đã hủy quá trình xử lý hóa đơn.")
    return ConversationHandler.END


async def cmd_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return
        
    user_id = update.effective_user.id
    
    text = update.message.text.strip()
    raw_args = text[9:].strip() # bỏ phần '/expense '
    
    if not raw_args:
        await update.message.reply_text(
            "Cú pháp: `/expense [Số tiền] [Tên_cửa_hàng]`\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng`\n",
            parse_mode="Markdown"
        )
        return

    args = raw_args.split()
    if len(args) < 2:
        await update.message.reply_text(
            "Cú pháp: `/expense [Số tiền] [Tên_cửa_hàng]`\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng`\n"
            "(Cần tối thiểu số tiền và tên cửa hàng)", 
            parse_mode="Markdown"
        )
        return

    try:
        amount_str = args[0].replace(',', '').replace('.', '')
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Số tiền không hợp lệ.")
        return

    store_name = " ".join(args[1:])
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    is_dup = is_duplicate(store_name, today_str, amount)

    data = {
        "is_invoice": True,
        "store_name": store_name,
        "date": today_str,
        "items": [],
        "total_amount": amount,
        "category": "Không phân loại",
        "is_suspicious_duplicate": is_dup
    }

    # Queue instantly
    invoice_id = save_invoice(user_id, data, status='pending')

    msg = f"✅ *Đã lưu hóa đơn thủ công vào bản nháp chờ duyệt*\n"
    if is_dup:
        msg = f"⚠️ *Cảnh báo:* Hóa đơn này có dấu hiệu trùng lặp nhưng vẫn được lưu. Kế toán sẽ kiểm tra lại.\n\n" + msg
    msg += f"Mã hóa đơn: #{invoice_id}\nCửa hàng: {store_name}\nSố tiền: {amount:,.0f} đ"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return
    user_id = update.effective_user.id
    rows = get_history(user_id, limit=5)
    text = format_history(rows)
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👨‍💻 *HƯỚNG DẪN SỬ DỤNG*\n\n"
        "📸 *Gửi ảnh:* Gửi trực tiếp ảnh hóa đơn để trích xuất và lưu nháp.\n"
        "🖊️ Dùng /expense [số tiền] [Tên] để nhập thủ công.\n"
        "Ví dụ: `/expense 50000 Cơm trưa văn phòng`\n"
        "📜 /history: Xem lại 5 hóa đơn gần nhất bạn đã gửi.\n"
        "❓ /help: Hiển thị bảng trợ giúp này."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return
    await update.message.reply_text("📸 Vui lòng gửi ảnh hóa đơn để xử lý.")

# ── Khởi chạy bot ─────────────────────────────────────────────────────────────

def main():
    init_db()
    logger.info("Database đã sẵn sàng.")

    async def post_init(application):
        """Thiết lập menu lệnh riêng biệt cho Admin và Nhân viên."""
        # Menu chung cho Nhân viên
        staff_commands = [
            BotCommand("help",    "Hiển thị bảng hướng dẫn"),
            BotCommand("history", "Xem lịch sử cá nhân"),
            BotCommand("expense", "Nhập hóa đơn thủ công"),
        ]
        await application.bot.set_my_commands(staff_commands, scope=BotCommandScopeDefault())
        logger.info("Hệ thống menu đã được thiết lập.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    photo_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={
            WAIT_PHOTO_CONFIRM: [
                CallbackQueryHandler(photo_confirm_callback, pattern="^(confirm_correct|edit_invoice)$")
            ],
            WAIT_PHOTO_EDIT: [
                MessageHandler(filters.TEXT, photo_edit_handler)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_photo)],
        per_message=False
    )
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(photo_conv_handler)
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("expense", cmd_expense))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo))

    logger.info("BizBot đang chạy... Bấm Ctrl+C để dừng.")
    app.run_polling()

if __name__ == "__main__":
    main()
