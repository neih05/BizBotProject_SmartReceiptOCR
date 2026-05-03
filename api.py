import os
import sqlite3
import json
import hashlib
import csv
import io
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import jwt

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_PATH = "invoices.db"

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

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

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return username

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM web_users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
        
    pwd_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if user['password_hash'] != pwd_hash:
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {"sub": user['username'], "role": user['role'], "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer", "role": user['role']}

@app.get("/api/invoices")
def get_invoices(current_user: str = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, e.real_name as sender_name 
        FROM invoices i 
        LEFT JOIN employees e ON CAST(i.user_id AS TEXT) = e.employee_id
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
async def update_invoice_status(invoice_id: int, update_data: InvoiceUpdate, current_user: str = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if invoice exists
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    invoice = cursor.fetchone()
    if not invoice:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    invoice_dict = dict(invoice)
    
    # Update raw_json with accounting info
    current_raw = json.loads(invoice_dict['raw_json'] or '{}')
    current_raw['category'] = update_data.category
    current_raw['debitAccount'] = update_data.debitAccount
    current_raw['creditAccount'] = update_data.creditAccount
    current_raw['department'] = update_data.department
    current_raw['notes'] = update_data.notes
    
    # Update status, amount and raw_json
    cursor.execute("""
        UPDATE invoices 
        SET status = ?, total_amount = ?, raw_json = ? 
        WHERE id = ?
    """, (update_data.status, update_data.totalAmount, json.dumps(current_raw), invoice_id))
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
def get_employees(current_user: str = Depends(get_current_user)):
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
        is_active = e_dict.get('is_active', 1)
        
        result.append({
            "id": e_dict['id'],
            "telegramId": e_dict['employee_id'],
            "name": e_dict['real_name'],
            "department": "Hành chính",
            "invoicesSent": stats.get('invoice_count', 0),
            "totalValue": stats.get('total_value', 0) or 0,
            "status": "approved" if is_active else "disabled",
            "isActive": bool(is_active)
        })
        
    return result

@app.post("/api/employees")
def add_employee(emp: EmployeeCreate, current_user: str = Depends(get_current_user)):
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


class EmployeeStatusUpdate(BaseModel):
    is_active: bool

@app.put("/api/employees/{employee_id}/status")
async def update_employee_status(employee_id: int, update: EmployeeStatusUpdate, current_user: str = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get employee_id (telegram id) before update
    cursor.execute("SELECT employee_id FROM employees WHERE id = ?", (employee_id,))
    emp = cursor.fetchone()
    
    cursor.execute("UPDATE employees SET is_active = ? WHERE id = ?", (int(update.is_active), employee_id))
    conn.commit()
    conn.close()
    
    # Send telegram message if disabled
    if not update.is_active and emp:
        tg_id = emp['employee_id']
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": tg_id,
            "text": "⛔ *Truy cập bị từ chối*\nBạn chưa được cấp quyền truy cập hệ thống hoặc quyền đã bị thu hồi. Nếu có thắc mắc vui lòng liên hệ kế toán.",
            "parse_mode": "Markdown"
        }
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"Error sending disable notification to {tg_id}: {e}")
                
    return {"success": True, "message": "Cập nhật trạng thái thành công"}

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
def get_stats(current_user: str = Depends(get_current_user)):
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

@app.get("/api/export")
def export_csv(
    status: str = None, 
    department: str = None, 
    maxAmount: float = None, 
    senders: str = None,
    current_user: str = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT i.*, e.real_name as sender_name 
        FROM invoices i 
        LEFT JOIN employees e ON CAST(i.user_id AS TEXT) = e.employee_id
        WHERE 1=1
    """
    params = []
    
    if status and status != "Tất cả trạng thái":
        db_status = "approved" if status == "Đã hạch toán" else ("pending" if status == "Chờ xử lý" else "rejected")
        query += " AND i.status = ?"
        params.append(db_status)
        
    if maxAmount is not None:
        query += " AND (i.total_amount IS NULL OR i.total_amount <= ?)"
        params.append(maxAmount)
        
    if senders:
        sender_list = [s for s in senders.split(',') if s.strip()]
        if sender_list:
            query += f" AND CAST(i.user_id AS TEXT) IN ({','.join(['?']*len(sender_list))})"
            params.extend(sender_list)
            
    query += " ORDER BY i.id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Mã HĐ', 'Ngày', 'Người gửi', 'Nhà cung cấp', 'Mã số thuế', 'Số hóa đơn', 'Loại CP', 'Thành tiền', 'Trạng thái', 'Ghi chú'])

    for row in rows:
        r = dict(row)
        try:
            ocr_data = json.loads(r.get('raw_json') or '{}')
        except:
            ocr_data = {}
            
        if department and department != "Tất cả phòng ban":
            if ocr_data.get("department") != department:
                continue
        
        writer.writerow([
            r['id'],
            r['date'],
            r.get('sender_name') or r['user_id'],
            r['store_name'],
            ocr_data.get('taxCode', ''),
            ocr_data.get('invNo', ''),
            ocr_data.get('category', ''),
            r['total_amount'],
            r['status'],
            ocr_data.get('notes', '')
        ])
    
    csv_content = "\ufeff" + output.getvalue()  # Add BOM for Excel UTF-8
    
    from fastapi.responses import Response
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bao_cao_chi_phi.csv"}
    )

@app.get("/api/charts")
def get_charts(current_user: str = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Pie chart
    cursor.execute("SELECT raw_json, total_amount FROM invoices WHERE status = 'approved'")
    approved_invoices = cursor.fetchall()
    category_totals = {}
    for inv in approved_invoices:
        try:
            ocr = json.loads(inv['raw_json'] or '{}')
            cat = ocr.get('category') or 'Khác'
            if not cat: cat = 'Khác'
            category_totals[cat] = category_totals.get(cat, 0) + (inv['total_amount'] or 0)
        except: pass
    pie_data = [{"name": k, "value": v} for k, v in category_totals.items() if v > 0]
    
    # 2. Bar chart data aggregations
    cursor.execute("SELECT date, raw_json, total_amount FROM invoices WHERE status = 'approved'")
    all_approved = cursor.fetchall()
    
    day_map = {}
    month_map = {}
    quarter_map = {}
    
    for inv in all_approved:
        date_str = inv['date']
        if not date_str or '/' not in date_str: continue
        amount = inv['total_amount'] or 0
        try:
            ocr = json.loads(inv['raw_json'] or '{}')
            cat = ocr.get('category') or 'Khác'
            if not cat: cat = 'Khác'
            
            # Day level
            if date_str not in day_map: day_map[date_str] = {}
            day_map[date_str][cat] = day_map[date_str].get(cat, 0) + amount
            
            # Month level (DD/MM/YYYY -> MM/YYYY)
            parts = date_str.split('/')
            if len(parts) == 3:
                m_key = f"{parts[1]}/{parts[2]}"
                if m_key not in month_map: month_map[m_key] = {}
                month_map[m_key][cat] = month_map[m_key].get(cat, 0) + amount
                
                # Quarter level
                q = (int(parts[1]) - 1) // 3 + 1
                q_key = f"Q{q}/{parts[2]}"
                if q_key not in quarter_map: quarter_map[q_key] = {}
                quarter_map[q_key][cat] = quarter_map[q_key].get(cat, 0) + amount
        except: pass

    def to_chart_list(d_map, limit, is_date=False):
        if is_date:
            # Sort by actual date for DD/MM/YYYY
            keys = sorted(d_map.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))[-limit:]
        else:
            # Monthly (MM/YYYY) and Quarterly (QX/YYYY) sort naturally with string sort if years are same
            # but let's at least sort them
            keys = sorted(d_map.keys())[-limit:]
        return [{"name": k, **d_map[k]} for k in keys]

    conn.close()
    return {
        "week": to_chart_list(day_map, 7, is_date=True),
        "month": to_chart_list(month_map, 6),
        "quarter": to_chart_list(quarter_map, 4),
        "categories": pie_data
    }

@app.get("/api/export-excel")
def export_excel(
    status: str = None, 
    department: str = None, 
    maxAmount: float = None, 
    senders: str = None,
    current_user: str = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT i.id, i.date, e.real_name as sender_name, 
               i.store_name, i.total_amount, i.status, i.raw_json, i.user_id
        FROM invoices i 
        LEFT JOIN employees e ON CAST(i.user_id AS TEXT) = e.employee_id
        WHERE 1=1
    """
    params = []
    
    if status and status != "Tất cả trạng thái":
        db_status = "approved" if status == "Đã hạch toán" else ("pending" if status == "Chờ xử lý" else "rejected")
        query += " AND i.status = ?"
        params.append(db_status)
        
    if maxAmount is not None:
        query += " AND (i.total_amount IS NULL OR i.total_amount <= ?)"
        params.append(maxAmount)
        
    if senders:
        sender_list = [s for s in senders.split(',') if s.strip()]
        if sender_list:
            query += f" AND CAST(i.user_id AS TEXT) IN ({','.join(['?']*len(sender_list))})"
            params.extend(sender_list)
            
    query += " ORDER BY i.id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    data = []
    for r in rows:
        row_dict = dict(r)
        try:
            ocr = json.loads(row_dict.pop('raw_json') or '{}')
            
            if department and department != "Tất cả phòng ban":
                if ocr.get("department") != department:
                    continue
                    
            row_dict['category'] = ocr.get('category', 'Khác')
            row_dict['notes'] = ocr.get('notes', '')
        except:
            if department and department != "Tất cả phòng ban":
                continue
            row_dict['category'] = 'Khác'
            row_dict['notes'] = ''
            
        row_dict.pop('user_id', None)
        data.append(row_dict)
        
    df = pd.DataFrame(data)
    
    # Rename columns for display
    column_mapping = {
        'id': 'Mã HĐ',
        'date': 'Ngày',
        'sender_name': 'Người gửi',
        'store_name': 'Nhà cung cấp',
        'category': 'Loại CP',
        'total_amount': 'Thành tiền',
        'status': 'Trạng thái',
        'notes': 'Ghi chú'
    }
    df = df.rename(columns=column_mapping)
    
    # Ensure correct column order
    cols = ['Mã HĐ', 'Ngày', 'Người gửi', 'Nhà cung cấp', 'Loại CP', 'Thành tiền', 'Trạng thái', 'Ghi chú']
    df = df[cols]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Báo cáo chi phí')
    
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bao_cao_chi_phi.xlsx"}
    )
