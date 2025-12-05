# keep_alive.py - Render uchun optimallashtirilgan

from flask import Flask
from threading import Thread
import time
import requests
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def start_keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Asosiy dastur tugasa, thread ham tugashi uchun
    t.start()
    print("✅ Keep-alive server started on port 8080")

# Render uchun ping funksiyasi
def ping_server():
    # Render da SERVICE_NAME environment variable bo'lishi mumkin
    service_name = os.getenv('RENDER_SERVICE_NAME', 'usta-elbek')
    
    while True:
        try:
            # Agar Render da bo'lsa
            if os.getenv('RENDER'):
                # Render hosting URL
                render_url = f"https://{service_name}.onrender.com"
                print(f"🔄 Pinging {render_url}")
                requests.get(render_url, timeout=10)
            time.sleep(60)  # 1 daqiqada bir (Render'da 5 daqiqa emas)
        except Exception as e:
            print(f"⚠️ Ping error: {e}")
            time.sleep(300)  # Xatolikda 5 daqiqaga uxlab qolish