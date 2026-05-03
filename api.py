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

@app.get("/api/employees")
def get_employees():
    conn = get_db()
    cursor = conn.cursor()
    # Lấy thông tin user có hóa đơn
    cursor.execute("""
        SELECT u.telegram_id, u.full_name, u.role, u.is_verified,
               COUNT(i.id) as invoice_count,
               SUM(CASE WHEN i.status = 'approved' THEN i.total_amount ELSE 0 END) as total_value
        FROM users u
        LEFT JOIN invoices i ON u.telegram_id = i.user_id
        GROUP BY u.telegram_id, u.full_name, u.role, u.is_verified
    """)
    users = cursor.fetchall()
    
    # Lấy thông tin employees table
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    
    conn.close()
    
    # Merge them for display
    emp_map = {str(e['employee_id']): dict(e) for e in employees}
    
    result = []
    for u in users:
        u_dict = dict(u)
        tid = str(u_dict['telegram_id'])
        emp_info = emp_map.get(tid, {})
        
        result.append({
            "id": u_dict['telegram_id'],
            "telegramId": u_dict['telegram_id'],
            "name": u_dict['full_name'],
            "nickname": emp_info.get('nickname', 'Không rõ'),
            "department": "Kế toán" if u_dict['role'] == 'admin' else "Hành chính",
            "invoicesSent": u_dict['invoice_count'],
            "totalValue": u_dict['total_value'] or 0,
            "status": "approved" if u_dict['is_verified'] else "pending"
        })
        
    return result

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
