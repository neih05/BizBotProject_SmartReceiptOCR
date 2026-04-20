import os
from dotenv import load_dotenv

load_dotenv() # Nạp biến từ file .env vào hệ thống

print(f"Token Telegram: {os.getenv('TELEGRAM_TOKEN')}")
print(f"Key Gemini: {os.getenv('GEMINI_API_KEY')}")