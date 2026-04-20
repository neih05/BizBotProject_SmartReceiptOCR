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
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.commit()
    conn.close()

def save_invoice(user_id: int, data: dict) -> int:
    """Lưu hóa đơn vào database, trả về id vừa insert."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (user_id, store_name, date, items, total_amount, raw_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("store_name", "Không rõ"),
        data.get("date", "Không rõ"),
        json.dumps(data.get("items", []), ensure_ascii=False),
        data.get("total_amount", 0),
        json.dumps(data, ensure_ascii=False)
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

def is_duplicate(user_id: int, store_name: str, date: str, total_amount: float) -> bool:
    """Kiểm tra xem hóa đơn đã tồn tại chưa (dựa trên store_name, date, total_amount)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM invoices 
        WHERE user_id = ? AND store_name = ? AND date = ? AND total_amount = ?
    """, (user_id, store_name, date, total_amount))
    row = cursor.fetchone()
    conn.close()
    return row is not None
