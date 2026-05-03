import json
import google.generativeai as genai
from PIL import Image
import io

PROMPT = """
Bạn là trợ lý phân tích hóa đơn. Hãy đọc ảnh hóa đơn này và trả về DUY NHẤT một JSON hợp lệ, 
không có thêm bất kỳ văn bản nào khác trước hoặc sau.

Cấu trúc JSON cần trả về:
{
  "is_invoice": true/false (chỉ trả về true nếu ảnh thực sự là hóa đơn/biên lai, false nếu là ảnh người, động vật, phong cảnh, v.v.),
  "store_name": "tên cửa hàng hoặc null nếu không rõ",
  "date": "ngày tháng năm dạng DD/MM/YYYY hoặc null nếu không rõ",
  "category": "danh mục chi tiêu (chỉ trả về 1 trong các tùy chọn: 'Ăn uống', 'Đi lại', 'Tiếp khách', 'Mua sắm vật tư', 'Khác' hoặc null nếu không thể phân loại)",
  "items": [
    {
      "name": "tên sản phẩm",
      "quantity": số lượng (số nguyên),
      "price": đơn giá (số thực)
    }
  ],
  "total_amount": tổng tiền (số thực)
}

Lưu ý:
- Nếu is_invoice là false, các trường còn lại có thể để null hoặc mảng rỗng.
- Nếu không đọc được thông tin nào, để giá trị là null
- Số tiền không có dấu phẩy hay chữ, chỉ là số thuần (ví dụ: 150000 không phải "150,000đ")
- Trả về JSON thuần túy, không có markdown, không có giải thích
"""

def setup_gemini(api_key: str):
    """Cấu hình Gemini API."""
    genai.configure(api_key=api_key)

def extract_invoice(image_bytes: bytes) -> dict:
    """
    Gửi ảnh lên Gemini để trích xuất thông tin hóa đơn.
    Trả về dict với dữ liệu hóa đơn hoặc raise Exception nếu lỗi.
    """
    model = genai.GenerativeModel("gemini-3-flash-preview")

    image = Image.open(io.BytesIO(image_bytes))

    response = model.generate_content(
        [PROMPT, image],
        generation_config={"response_mime_type": "application/json"}
    )
    
    data = json.loads(response.text)
    return data

def categorize_text(text: str) -> str:
    """
    Gửi đoạn text (tên cửa hàng/chi phí) lên Gemini để dự đoán danh mục.
    """
    model = genai.GenerativeModel("gemini-3-flash-preview")
    prompt = f"""
    Bạn là kế toán viên. Hãy phân loại khoản chi phí sau vào 1 trong các danh mục: 
    'Ăn uống', 'Đi lại', 'Tiếp khách', 'Mua sắm vật tư', 'Khác'.
    Chỉ trả về ĐÚNG TÊN DANH MỤC, không thêm bất kỳ ký tự nào khác.
    
    Khoản chi phí: "{text}"
    """
    try:
        response = model.generate_content(prompt)
        cat = response.text.strip()
        valid_cats = ['Ăn uống', 'Đi lại', 'Tiếp khách', 'Mua sắm vật tư', 'Khác']
        for c in valid_cats:
            if c.lower() in cat.lower():
                return c
        return 'Khác'
    except:
        return 'Khác'
