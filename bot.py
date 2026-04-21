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
    get_all_invoices_for_export, get_daily_report
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
WAIT_PHOTO_CONFIRM = 3
WAIT_PHOTO_EDIT = 4
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
            "✏️ Dùng /expense [số tiền] [Tên] - [Danh mục] để nhập tay.\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng - Ăn uống`",
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
            result_text = "⚠️ *Hóa đơn này có vẻ đã được gửi trước đó trên hệ thống. Vui lòng kiểm tra lại.*\n\n" + result_text
            
        result_text += f"\n\nDanh mục: {category_str}. Xác nhận?"

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
                f"Vui lòng vào /pending để xem xét và duyệt."
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
            "`/expense [Số tiền] [Tên cửa hàng] - [Danh mục]`\n"
            "(Tên cửa hàng và Danh mục là không bắt buộc)\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng - Ăn uống`",
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
        if " - " in raw_args:
            main_part, category = raw_args.split(" - ", 1)
        else:
            main_part = raw_args
            category = user_data.get("category", "Khác")
            
        args = main_part.split()
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Cú pháp không hợp lệ. Vui lòng gõ lại theo định dạng:\n"
                "`/expense [Số tiền] [Tên_cửa_hàng] - [Danh_mục]`\n"
                "Ví dụ: `/expense 50000 Cơm trưa văn phòng - Ăn uống`",
                parse_mode="Markdown"
            )
            return WAIT_PHOTO_EDIT
            
        amount_str = args[0]
        store_name = " ".join(args[1:]) if len(args) > 1 else user_data.get("store_name", "Không rõ")
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
        f"Mã hóa đơn chờ duyệt: #{invoice_id}\nCửa hàng: {store_name}\nDanh mục: {category}\nSố tiền mới: {amount:,.0f} đ",
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
            "Cú pháp: `/expense [Số tiền] [Tên_cửa_hàng] - [Danh_mục]`\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng - Ăn uống`\n"
            "(Danh mục không bắt buộc)", 
            parse_mode="Markdown"
        )
        return

    if " - " in raw_args:
        main_part, category = raw_args.split(" - ", 1)
    else:
        main_part = raw_args
        category = "Khác"

    args = main_part.split()
    if len(args) < 2:
        await update.message.reply_text(
            "Cú pháp: `/expense [Số tiền] [Tên_cửa_hàng] - [Danh_mục]`\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng - Ăn uống`\n"
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

    data = {
        "is_invoice": True,
        "store_name": store_name,
        "date": today_str,
        "items": [],
        "total_amount": amount,
        "category": category
    }

    # Queue instantly
    invoice_id = save_invoice(user_id, data, status='pending')

    await update.message.reply_text(
        f"✅ *Đã lưu hóa đơn thủ công vào bản nháp chờ duyệt*\n"
        f"Mã hóa đơn: #{invoice_id}\nCửa hàng: {store_name}\nDanh mục: {category}\nSố tiền: {amount:,.0f} đ",
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
            "📊 /report: Báo cáo nhanh chi tiêu trong ngày.\n"
            "📥 /export: Xuất toàn bộ dữ liệu hóa đơn chi tiết (Tất cả ngày).\n"
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
            "🖊️ Dùng /expense [số tiền] [Tên] - [Danh mục] để nhập thủ công.\n"
            "Ví dụ: `/expense 50000 Cơm trưa văn phòng - Ăn uống`\n"
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
        is_dup = is_duplicate(inv["store_name"], inv["date"], inv["total_amount"], exclude_id=inv["id"])
        
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

    # Nếu có truyền tham số ngày (VD: /report 20/04/2026)
    args = context.args
    if args and len(args) > 0:
        target_date_str = args[0]
    else:
        target_date_str = datetime.now().strftime("%d/%m/%Y")

    report = get_daily_report(target_date_str)
    
    if report["count"] == 0:
        await update.message.reply_text(f"📊 Báo cáo ngày ({target_date_str}):\nKhông có hóa đơn nào được duyệt trong ngày.")
        return
        
    text = (
        f"📊 *BÁO CÁO NGÀY ({target_date_str})*\n"
        f"─" * 20 + "\n"
        f"💰 *Tổng chi tiêu:* {report['total']:,.0f} VNĐ\n"
        f"🧾 *Số lượng hóa đơn:* {report['count']}\n\n"
    )
    
    top = report["top_invoice"]
    if top:
        try:
            raw_data = json.loads(top.get('raw_json') or '{}')
            cat = raw_data.get('category', 'Không rõ')
        except:
            cat = 'Không rõ'
            
        text += (
            f"🔥 *CHI TIÊU NHIỀU NHẤT HÔM NAY*\n"
            f"🏪 Cửa hàng: {top['store_name']}\n"
            f"🏷️ Danh mục: {cat}\n"
            f"💸 Số tiền: {top['total_amount']:,.0f} VNĐ"
        )
        
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return

    all_invoices = get_all_invoices_for_export()
    if not all_invoices:
        await update.message.reply_text("Không có dữ liệu hóa đơn nào trong hệ thống.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_chi_phi_{timestamp}.csv"
    
    with open(filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Người Gửi", "Số Tiền", "Danh Mục", "Ngày Tháng", "Cửa Hàng", "Trạng Thái"])
        for row in all_invoices:
            sender = row.get("sender_name") or f"ID: {row.get('user_id', '?')}"
            writer.writerow([
                row["id"], 
                sender, 
                row["total_amount"], 
                row["category"], 
                row["date"],
                row["store_name"],
                row["status"]
            ])

    await context.bot.send_document(
        chat_id=user_id,
        document=open(filename, "rb"),
        filename=filename,
        caption=f"📁 Xuất toàn bộ dữ liệu hóa đơn chi tiết (Tạo lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')})."
    )
    os.remove(filename)

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
            BotCommand("report",  "Báo cáo nhanh hôm nay"),
            BotCommand("export",  "Xuất tất cả dữ liệu"),
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
    
    app.add_handler(conv_handler)
    app.add_handler(photo_conv_handler)
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("expense", cmd_expense))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("report",  cmd_report))
    app.add_handler(CommandHandler("export",  cmd_export))
    app.add_handler(CommandHandler("users",   cmd_users))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve_|reject_)"))

    logger.info("BizBot đang chạy... Bấm Ctrl+C để dừng.")
    app.run_polling()

if __name__ == "__main__":
    main()
