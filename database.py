import sqlite3
import json
from datetime import datetime

DB_PATH = "invoices.db"

def init_db():
    """Khởi tạo database và tạo bảng nếu chưa có."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            store_name  TEXT,
            date        TEXT,
            items       TEXT,
            total_amount REAL,
            raw_json    TEXT,
            status      TEXT DEFAULT 'pending',
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id  INTEGER PRIMARY KEY,
            full_name    TEXT,
            company_code TEXT,
            role         TEXT,
            is_verified  BOOLEAN DEFAULT 0
        )
    """)
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN status TEXT DEFAULT 'pending'")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def save_invoice(user_id: int, data: dict, status: str = 'pending') -> int:
    """Lưu hóa đơn vào database, trả về id vừa insert."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (user_id, store_name, date, items, total_amount, raw_json, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("store_name", "Không rõ"),
        data.get("date", "Không rõ"),
        json.dumps(data.get("items", []), ensure_ascii=False),
        data.get("total_amount", 0),
        json.dumps(data, ensure_ascii=False),
        status
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_history(user_id: int, limit: int = 5) -> list:
    """Lấy N hóa đơn gần nhất của user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, store_name, date, total_amount, created_at
        FROM invoices
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def count_user_invoices(user_id: int) -> int:
    """Đếm tổng số hóa đơn của một user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def is_duplicate(store_name: str, date: str, total_amount: float, exclude_id: int = None) -> bool:
    """Kiểm tra xem hóa đơn đã tồn tại chưa (dựa trên store_name, date, total_amount)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT id FROM invoices 
        WHERE store_name = ? AND date = ? AND total_amount = ? AND status != 'rejected'
    """
    params = [store_name, date, total_amount]
    
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
        
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_user(telegram_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_user(telegram_id: int, full_name: str, company_code: str, role: str, is_verified: bool = False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (telegram_id, full_name, company_code, role, is_verified)
        VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, full_name, company_code, role, is_verified))
    conn.commit()
    conn.close()

def update_user_status(telegram_id: int, is_verified: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_verified = ? WHERE telegram_id = ?", (is_verified, telegram_id))
    conn.commit()
    conn.close()

def get_pending_invoices() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, store_name, date, total_amount, created_at, raw_json
        FROM invoices
        WHERE status = 'pending'
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_invoice_status(invoice_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
    conn.commit()
    conn.close()

def get_approved_invoices_for_report() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.user_id as staff_id, u.full_name, SUM(i.total_amount) as total_amount, COUNT(i.id) as count
        FROM invoices i
        LEFT JOIN users u ON i.user_id = u.telegram_id
        WHERE i.status = 'approved'
        GROUP BY i.user_id, u.full_name
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_users_with_stats() -> list:
    """Lấy danh sách nhân viên (staff) kèm số lượng hóa đơn họ đã gửi."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.telegram_id, u.full_name, u.role, u.is_verified,
               COUNT(i.id) as invoice_count
        FROM users u
        LEFT JOIN invoices i ON u.telegram_id = i.user_id
        GROUP BY u.telegram_id, u.full_name, u.role, u.is_verified
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_invoices_for_export() -> list:
    """Truy vấn tất cả hóa đơn để xuất file Excel/CSV."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            i.id,
            u.full_name as sender_name,
            i.total_amount,
            i.raw_json,
            i.date,
            i.store_name,
            i.status
        FROM invoices i
        LEFT JOIN users u ON i.user_id = u.telegram_id
        ORDER BY i.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        r = dict(row)
        try:
            raw_data = json.loads(r.get('raw_json') or '{}')
            r['category'] = raw_data.get('category', 'Đóng góp/Khác')
        except:
            r['category'] = 'Không rõ'
        result.append(r)
        
    return result

def get_daily_report(date_str: str) -> dict:
    """Lấy báo cáo tổng chi tiêu trong ngày và hóa đơn đắt nhất."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(total_amount) as total, COUNT(id) as count
        FROM invoices 
        WHERE date = ? AND status = 'approved'
    """, (date_str,))
    summary = cursor.fetchone()
    
    cursor.execute("""
        SELECT store_name, total_amount, raw_json
        FROM invoices
        WHERE date = ? AND status = 'approved'
        ORDER BY total_amount DESC
        LIMIT 1
    """, (date_str,))
    top_invoice = cursor.fetchone()
    
    conn.close()
    
    return {
        "total": summary["total"] if summary and summary["total"] else 0,
        "count": summary["count"] if summary and summary["count"] else 0,
        "top_invoice": dict(top_invoice) if top_invoice else None
    }


