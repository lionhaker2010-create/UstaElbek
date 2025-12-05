# keep_alive.py - Kuchliroq ping tizimi

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
    app.run(host='0.0.0.0', port=10000, debug=False, threaded=True)

def start_keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
    print("✅ Keep-alive server started on port 10000")
    return t

def auto_ping():
    """Kuchliroq ping tizimi - uxlab qolishning oldini olish"""
    
    ping_urls = [
        "https://ustaelbek.onrender.com",
        "https://ustaelbek.onrender.com/ping",
        "https://ustaelbek.onrender.com/health"
    ]
    
    while True:
        try:
            if os.getenv('RENDER'):
                for url in ping_urls:
                    try:
                        response = requests.get(url, timeout=10)
                        print(f"🔄 Pinged {url}: {response.status_code}")
                    except:
                        pass
                
                # Qo'shimcha: External monitoring services
                try:
                    # UptimeRobot (agar ulangan bo'lsa)
                    requests.get("https://api.uptimerobot.com/v2/getMonitors", timeout=5)
                except:
                    pass
                
                # 4 daqiqada bir (240 soniya)
                time.sleep(240)
                
        except Exception as e:
            print(f"⚠️ Auto-ping error: {e}")
            time.sleep(60)