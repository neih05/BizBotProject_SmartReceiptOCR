def format_invoice(data: dict) -> str:
    """
    Format dữ liệu hóa đơn thành text đẹp để reply Telegram.
    """
    lines = []
    lines.append("🧾 *KẾT QUẢ TRÍCH XUẤT HÓA ĐƠN*")
    lines.append("─" * 30)

    store = data.get("store_name") or "Không rõ"
    date  = data.get("date")       or "Không rõ"
    category = data.get("category") or "Khác"
    
    lines.append(f"🏪 *Cửa hàng:* {store}")
    lines.append(f"📅 *Ngày:*      {date}")
    lines.append(f"🏷️ *Danh mục:*  {category}")
    lines.append("")

    items = data.get("items", [])
    if items:
        lines.append("📦 *Danh sách hàng:*")
        for item in items:
            name     = item.get("name", "?")
            qty      = item.get("quantity", 1)
            price    = item.get("price", 0) or 0
            subtotal = qty * price
            lines.append(
                f"  • {name}\n"
                f"    {qty} x {price:,.0f}đ = *{subtotal:,.0f}đ*"
            )
    else:
        lines.append("📦 *Danh sách hàng:* Không trích xuất được")

    lines.append("")
    lines.append("─" * 30)
    total = data.get("total_amount") or 0
    lines.append(f"💰 *TỔNG CỘNG: {total:,.0f}đ*")

    return "\n".join(lines)


def format_history(rows: list) -> str:
    """
    Format danh sách hóa đơn lịch sử.
    rows: [(id, store_name, date, total_amount, created_at), ...]
    """
    if not rows:
        return "📭 Bạn chưa có hóa đơn nào được lưu."

    lines = ["📋 *5 HÓA ĐƠN GẦN NHẤT*", "─" * 30]
    for i, (inv_id, store, date, total, created_at) in enumerate(rows, 1):
        store = store or "Không rõ"
        date  = date  or "Không rõ"
        total = total or 0
        lines.append(
            f"*{i}.* #{inv_id} — {store}\n"
            f"    📅 {date}  |  💰 {total:,.0f}đ\n"
            f"    🕐 Lưu lúc: {created_at}"
        )
        if i < len(rows):
            lines.append("")
    return "\n".join(lines)
