import json
import re
import google.generativeai as genai
from PIL import Image
import io

PROMPT = """
Bạn là trợ lý phân tích hóa đơn. Hãy đọc ảnh hóa đơn này và trả về DUY NHẤT một JSON hợp lệ, 
không có thêm bất kỳ văn bản nào khác trước hoặc sau.

Cấu trúc JSON cần trả về:
{
  "store_name": "tên cửa hàng hoặc null nếu không rõ",
  "date": "ngày tháng năm dạng DD/MM/YYYY hoặc null nếu không rõ",
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
    model = genai.GenerativeModel("gemini-1.5-flash")

    image = Image.open(io.BytesIO(image_bytes))

    response = model.generate_content([PROMPT, image])
    raw_text = response.text.strip()

    # Xóa markdown code block nếu model trả về có ```json ... ```
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    data = json.loads(raw_text)
    return data
