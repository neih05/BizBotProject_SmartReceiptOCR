import os
import sqlite3
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_PATH = "invoices.db"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/invoices")
def get_invoices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, u.full_name as sender_name 
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
            r['ocr'] = json.loads(r.get('raw_json') or '{}')
        except:
            r['ocr'] = {}
        result.append(r)
    return result

class InvoiceUpdate(BaseModel):
    status: str
    debitAccount: str = ""
    creditAccount: str = ""
    category: str = ""
    department: str = ""
    notes: str = ""
    totalAmount: float = 0

@app.post("/api/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: int, update_data: InvoiceUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if invoice exists
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    invoice = cursor.fetchone()
    if not invoice:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    invoice_dict = dict(invoice)
    
    # Update status and amount
    cursor.execute("""
        UPDATE invoices 
        SET status = ?, total_amount = ? 
        WHERE id = ?
    """, (update_data.status, update_data.totalAmount, invoice_id))
    conn.commit()
    conn.close()
    
    # Send telegram notification
    status_text = "ĐƯỢC DUYỆT (Đã hạch toán)" if update_data.status == "approved" else "BỊ TỪ CHỐI"
    msg = f"🔔 Hóa đơn #{invoice_id} của bạn tại {invoice_dict['store_name']} vừa {status_text}.\n"
    if update_data.notes:
        msg += f"Ghi chú từ kế toán: {update_data.notes}"
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": invoice_dict["user_id"],
        "text": msg
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            print("Lỗi gửi tin nhắn Telegram:", e)
            
    return {"success": True, "message": "Updated successfully"}

class EmployeeCreate(BaseModel):
    employee_id: str
    real_name: str

@app.get("/api/employees")
def get_employees():
    conn = get_db()
    cursor = conn.cursor()
    
    # Lấy tất cả nhân viên từ bảng employees (nguồn chính)
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    
    # Lấy thống kê hóa đơn theo user
    cursor.execute("""
        SELECT user_id,
               COUNT(id) as invoice_count,
               SUM(CASE WHEN status = 'approved' THEN total_amount ELSE 0 END) as total_value
        FROM invoices
        GROUP BY user_id
    """)
    stats_rows = cursor.fetchall()
    stats_map = {str(s['user_id']): dict(s) for s in stats_rows}
    
    conn.close()
    
    result = []
    for e in employees:
        e_dict = dict(e)
        tid = str(e_dict['employee_id'])
        stats = stats_map.get(tid, {})
        
        result.append({
            "id": e_dict['id'],
            "telegramId": e_dict['employee_id'],
            "name": e_dict['real_name'],
            "department": "Hành chính",
            "invoicesSent": stats.get('invoice_count', 0),
            "totalValue": stats.get('total_value', 0) or 0,
            "status": "approved"
        })
        
    return result

@app.post("/api/employees")
def add_employee(emp: EmployeeCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Kiểm tra trùng
    cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (emp.employee_id,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Telegram ID này đã tồn tại trong hệ thống")
    
    cursor.execute(
        "INSERT INTO employees (employee_id, real_name) VALUES (?, ?)",
        (emp.employee_id, emp.real_name)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return {"success": True, "id": new_id, "message": "Thêm nhân viên thành công"}

@app.get("/api/telegram-image/{file_id}")
async def get_telegram_image(file_id: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            if res.status_code == 200:
                file_path = res.json()["result"]["file_path"]
                img_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                img_res = await client.get(img_url)
                from fastapi.responses import Response
                return Response(content=img_res.content, media_type="image/jpeg")
        except Exception as e:
            print(f"Error fetching telegram image: {e}")
            
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_amount), COUNT(id) FROM invoices WHERE status = 'approved' AND date LIKE '%' || strftime('%m/%Y', 'now') || '%'")
    month_stats = cursor.fetchone()
    
    cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE status = 'approved'")
    total_spent = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_spent_week": total_spent, 
        "pending_invoices": pending_count,
        "approved_month_count": month_stats[1] or 0,
        "approved_month_value": month_stats[0] or 0,
        "budget_warnings": 0
    }
