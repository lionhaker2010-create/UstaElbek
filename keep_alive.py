# keep_alive.py - Oddiy va ishonchli versiya

from flask import Flask
from threading import Thread
import time
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Usta Elbek Bot is alive!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/ping')
def ping():
    return "pong", 200

def run():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    return t

def ping_self():
    """O'z-o'zini ping qilish (Render uchun)"""
    service_name = os.getenv('RENDER_SERVICE_NAME', 'ustaelbek')
    
    while True:
        try:
            if os.getenv('RENDER'):
                url = f"https://{service_name}.onrender.com"
                requests.get(url, timeout=10)
            time.sleep(300)  # 5 daqiqada bir
        except:
            time.sleep(60)