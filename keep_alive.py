# keep_alive.py - Faqat asosiy sahifa uchun

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Usta Elbek Bot is alive!"

def start_keep_alive():
    # Flask ni ishga tushirmaymiz, chunki webhook allaqachon ishlaydi
    print("✅ Keep-alive endpoints registered")