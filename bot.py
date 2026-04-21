import os
import logging
import csv
from dotenv import load_dotenv

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
    update_invoice_status, get_approved_invoices_for_report, get_users_with_stats
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
ASK_CODE = 1
ASK_NAME = 2
AUTH_CODE = "BIZ_HANU_2026"


# ── Middleware kiểm tra User ──────────────────────────────────────────────────
async def check_user_verified(update: Update) -> bool:
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user["is_verified"]:
        await update.message.reply_text("⛔ Quyền truy cập bị từ chối: Bạn chưa được xác thực tài khoản. Vui lòng gõ /start để đăng nhập.")
        return False
    return True

# ── Handlers Chào Mừng & Xác Thực ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user and user["is_verified"]:
        await update.message.reply_text(
            f"👋 Xin chào {user['full_name']}! Bạn đã được cấp quyền.\n\n"
            "📸 Bạn có thể gửi ảnh hóa đơn cho tôi để đưa vào danh sách chờ duyệt.\n"
            "📋 Dùng /history để xem 5 hóa đơn gần nhất.\n"
            "✏️ Dùng /expense [số tiền] [Tên] để nhập tay.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    elif user and not user["is_verified"]:
        await update.message.reply_text("⏳ Tài khoản của bạn đang chờ Admin duyệt. Vui lòng kiên nhẫn...")
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "👋 Chào mừng bạn đến với *BizBot* — Hệ thống quản lý hóa đơn nội bộ.\n\n"
            "Vui lòng nhập *Mã Bảo Mật* để tiếp tục:",
            parse_mode="Markdown"
        )
        return ASK_CODE

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == AUTH_CODE:
        await update.message.reply_text("✅ Mã chính xác! Vui lòng nhập *Họ và Tên* của bạn:", parse_mode="Markdown")
        return ASK_NAME
    else:
        await update.message.reply_text("❌ Mã bảo mật không chính xác. Vui lòng gõ /start để thử lại.")
        return ConversationHandler.END

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Kiểm tra xem có phải Admin không
    is_admin = (user_id == ADMIN_ID)
    role = "admin" if is_admin else "staff"
    is_verified = True if is_admin else False
    
    save_user(user_id, name, "DEFAULT_COMPANY", role, is_verified)
    
    if is_admin:
        await update.message.reply_text(
            f"👋 Chào {name}! Hệ thống đã nhận diện bạn là Admin và kích hoạt toàn bộ quyền quản trị.\n\n"
            "Dùng /help để xem các lệnh dành cho Admin.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"Cảm ơn {name}. Yêu cầu cấp quyền của bạn đã được gửi cho Kế toán (Admin). Bạn sẽ nhận được thông báo khi được duyệt!"
    )
    
    # Gửi thông báo cho Admin
    keyboard = [
        [
            InlineKeyboardButton("Duyệt ✅", callback_data=f"approve_user_{user_id}"),
            InlineKeyboardButton("Từ chối ❌", callback_data=f"reject_user_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 *Yêu cầu cấp quyền mới*\n\nNhân viên: {name}\nTelegram ID: {user_id}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Lỗi gửi thông báo cho Admin: {e}")
        
    return ConversationHandler.END

async def cancel_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đã hủy quá trình đăng nhập.")
    return ConversationHandler.END


# ── Nghiệp vụ Hóa Đơn ────────────────────────────────────────────────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return
        
    user_id   = update.effective_user.id

    processing_msg = await update.message.reply_text("⏳ Đang phân tích hóa đơn, vui lòng chờ...")

    try:
        photo = update.message.photo[-1]
        file  = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        data = extract_invoice(bytes(image_bytes))

        if data.get("is_invoice") is False:
            await processing_msg.edit_text("⚠️ Đây không phải hóa đơn, vui lòng gửi lại ảnh khác.")
            return

        # Lưu nháp chờ duyệt
        invoice_id = save_invoice(user_id, data, status='pending')

        result_text = format_invoice(data)
        result_text += f"\n\n✅ *Hóa đơn đã được lưu vào bản nháp (Draft) chờ kế toán duyệt.* (Mã draft: #{invoice_id})"

        await processing_msg.edit_text(result_text, parse_mode="Markdown")

    except ValueError as e:
        logger.warning(f"Lỗi parse JSON: {e}")
        await processing_msg.edit_text("⚠️ Bot không đọc được thông tin. Hãy thử ảnh rõ hơn.")
    except Exception as e:
        logger.error(f"Lỗi không xác định: {e}", exc_info=True)
        await processing_msg.edit_text("❌ Đã xảy ra lỗi hệ thống.")


async def cmd_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return
        
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "Cú pháp: `/expense [Số tiền] [Tên_cửa_hàng]`\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng`", 
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

    data = {
        "is_invoice": True,
        "store_name": store_name,
        "date": today_str,
        "items": [],
        "total_amount": amount
    }

    # Queue instantly
    invoice_id = save_invoice(user_id, data, status='pending')

    await update.message.reply_text(
        f"✅ *Đã lưu hóa đơn thủ công vào bản nháp chờ duyệt*\n"
        f"Mã hóa đơn: #{invoice_id}\nCửa hàng: {store_name}\nSố tiền: {amount:,.0f} đ",
        parse_mode="Markdown"
    )

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_verified(update):
        return
    user_id = update.effective_user.id
    rows = get_history(user_id, limit=5)
    text = format_history(rows)
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        # Người lạ (chưa đăng ký)
        text = (
            "👋 *Chào mừng bạn đến với BizBot!*\n\n"
            "Hiện tại bạn chưa được cấp quyền sử dụng hệ thống.\n"
            "👉 Vui lòng gõ /start và nhập *Mã Bảo Mật* để đăng ký tham gia."
        )
    elif not user["is_verified"]:
        # Đã đăng ký nhưng chưa duyệt
        text = (
            "⏳ *Tài khoản đang chờ duyệt*\n\n"
            "Bạn đã gửi yêu cầu tham gia. Vui lòng chờ Admin (Kế toán) xác nhận.\n"
            "Chỉ sau khi được duyệt, bạn mới có thể sử dụng các chức năng của bot."
        )
    elif user["role"] == "admin":
        # Menu cho Admin
        text = (
            "🦸‍♂️ *MENU QUẢN TRỊ VIÊN (ADMIN)*\n\n"
            "📂 /pending: Xem và duyệt các hóa đơn đang chờ.\n"
            "📊 /report: Xuất báo cáo tổng hợp chi phí (file CSV).\n"
            "👥 /users: Xem danh sách nhân viên & thống kê hóa đơn.\n"
            "📜 /history: Xem lịch sử chi tiêu cá nhân.\n"
            "🖊️ /expense: Nhập chi tiêu cá nhân.\n"
            "❓ /help: Hiển thị bảng trợ giúp này."
        )
    else:
        # Menu cho Staff (đã verified)
        text = (
            "👨‍💻 *MENU NHÂN VIÊN*\n\n"
            "📸 *Gửi ảnh:* Gửi trực tiếp ảnh hóa đơn để trích xuất và lưu nháp.\n"
            "🖊️ /expense [số tiền] [nội dung]: Nhập hóa đơn thủ công khi không có ảnh.\n"
            "📜 /history: Xem lại 5 hóa đơn gần nhất bạn đã gửi.\n"
            "❓ /help: Hiển thị bảng trợ giúp này."
        )

    await update.message.reply_text(text, parse_mode="Markdown")


# ── Nghiệp vụ Admin ──────────────────────────────────────────────────────────

async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return

    pending_list = get_pending_invoices()
    if not pending_list:
        await update.message.reply_text("✅ Không có hóa đơn nào đang chờ duyệt.")
        return

    await update.message.reply_text(f"📋 Tìm thấy {len(pending_list)} hóa đơn chờ duyệt:")

    for inv in pending_list:
        user_info = get_user(inv["user_id"])
        user_name = user_info["full_name"] if user_info else f"ID: {inv['user_id']}"
        
        # Kiểm tra trùng lặp nhưng trừ chính nó ra
        is_dup = is_duplicate(inv["user_id"], inv["store_name"], inv["date"], inv["total_amount"], exclude_id=inv["id"])
        
        text = (
            f"🧾 *Mã Hóa Đơn:* #{inv['id']}\n"
            f"👤 *Nhân viên:* {user_name}\n"
            f"🏪 *Cửa hàng:* {inv['store_name']}\n"
            f"📅 *Ngày:* {inv['date']}\n"
            f"💰 *Tổng tiền:* {inv['total_amount']:,.0f} VND\n"
        )
        if is_dup:
            text += "⚠️ *CẢNH BÁO TRÙNG LẶP DỮ LIỆU!*\n"
            
        keyboard = [
            [
                InlineKeyboardButton("Duyệt ✅", callback_data=f"approve_invoice_{inv['id']}_{inv['user_id']}"),
                InlineKeyboardButton("Từ chối ❌", callback_data=f"reject_invoice_{inv['id']}_{inv['user_id']}")
            ]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return

    approved_list = get_approved_invoices_for_report()
    if not approved_list:
        await update.message.reply_text("Không có hóa đơn nào đã duyệt để xuất báo cáo.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bao_cao_chi_phi_{timestamp}.csv"
    filepath = filename

    with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Telegram ID", "Họ Tên", "Số Lượng Hóa Đơn", "Tổng Chi Phí (VND)"])
        for row in approved_list:
            writer.writerow([row["staff_id"], row["full_name"], row["count"], row["total_amount"]])

    await context.bot.send_document(
        chat_id=ADMIN_ID,
        document=open(filepath, "rb"),
        filename=filename,
        caption=f"📊 Báo cáo tổng hợp chi phí đã duyệt (Xuất lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')})."
    )
    os.remove(filepath)

async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /users dành cho Admin: Xem danh sách user và stats."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return

    users = get_users_with_stats()
    if not users:
        await update.message.reply_text("Chưa có người dùng nào trong hệ thống.")
        return

    text = "👥 *DANH SÁCH NHÂN VIÊN*\n\n"
    for u in users:
        status_icon = "✅" if u["is_verified"] else "⏳"
        role_label = "Admin" if u["role"] == "admin" else "Staff"
        text += (
            f"{status_icon} *{u['full_name']}* ({role_label})\n"
            f"   └ ID: `{u['telegram_id']}`\n"
            f"   └ Hóa đơn: {u['invoice_count']}\n\n"
        )
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("⛔ Bạn không có quyền duyệt!")
        return

    data = query.data

    if data.startswith("approve_user_"):
        target_user = int(data.split("_")[2])
        update_user_status(target_user, True)
        await query.edit_message_text(f"{query.message.text}\n\n✅ *Đã duyệt User*", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_user, text="🎉 Tài khoản của bạn đã được Kế toán duyệt! Bây giờ bạn có thể gửi ảnh hóa đơn.")
        except:
            pass
            
    elif data.startswith("reject_user_"):
        target_user = int(data.split("_")[2])
        await query.edit_message_text(f"{query.message.text}\n\n❌ *Đã từ chối User*", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_user, text="❌ Yêu cầu cấp quyền của bạn đã bị từ chối.")
        except:
            pass

    elif data.startswith("approve_invoice_"):
        parts = data.split("_")
        invoice_id = int(parts[2])
        target_user = int(parts[3])
        update_invoice_status(invoice_id, "approved")
        await query.edit_message_text(f"{query.message.text}\n\n✅ *Đã duyệt hóa đơn này.*", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_user, text=f"✅ Hóa đơn draft #{invoice_id} của bạn đã được Kế toán duyệt.")
        except:
            pass

    elif data.startswith("reject_invoice_"):
        parts = data.split("_")
        invoice_id = int(parts[2])
        target_user = int(parts[3])
        update_invoice_status(invoice_id, "rejected")
        await query.edit_message_text(f"{query.message.text}\n\n❌ *Đã từ chối hóa đơn này.*", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_user, text=f"❌ Hóa đơn draft #{invoice_id} của bạn đã bị Kế toán từ chối.")
        except:
            pass

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

        # Menu riêng cho Admin
        admin_commands = [
            BotCommand("help",    "Bảng điều khiển Admin"),
            BotCommand("pending", "Duyệt hóa đơn chờ"),
            BotCommand("report",  "Xuất báo cáo CSV"),
            BotCommand("users",   "Quản lý nhân viên"),
            BotCommand("history", "Lịch sử chi cá nhân"),
            BotCommand("expense", "Nhập chi cá nhân"),
        ]
        try:
            await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
            logger.info(f"Đã thiết lập menu riêng cho Admin ({ADMIN_ID})")
        except Exception as e:
            logger.warning(f"Không thể thiết lập menu Admin: {e}")

        logger.info("Hệ thống menu đã được phân quyền.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            ASK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel_auth)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("expense", cmd_expense))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("report",  cmd_report))
    app.add_handler(CommandHandler("users",   cmd_users))
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo))
    app.add_handler(CallbackQueryHandler(admin_callback))

    logger.info("BizBot đang chạy... Bấm Ctrl+C để dừng.")
    app.run_polling()

if __name__ == "__main__":
    main()
