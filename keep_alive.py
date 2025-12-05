# keep_alive.py - To'liq tuzatilgan versiya

from flask import Flask
from threading import Thread
import time
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is alive and running!"

@app.route('/health')
def health():
    return "✅ OK", 200

@app.route('/ping')
def ping():
    return "🏓 Pong!", 200

def run():
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8080)),
        debug=False
    )

def start_keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print(f"✅ Keep-alive server started on port {os.getenv('PORT', 8080)}")

# Render uchun avto-ping funksiyasi
def ping_render():
    """Render'da botni uxlatmaslik uchun"""
    render_service_name = os.getenv('RENDER_SERVICE_NAME', 'ustaelbek')
    
    while True:
        try:
            if os.getenv('RENDER', 'false').lower() == 'true':
                render_url = f"https://{render_service_name}.onrender.com"
                print(f"🔄 Pinging {render_url}")
                response = requests.get(render_url, timeout=30)
                print(f"✅ Ping successful: {response.status_code}")
            time.sleep(240)  # 4 daqiqada bir (Render free tier uchun)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Ping failed: {e}")
            time.sleep(60)  # Xatolikda 1 daqiqa kutish
        except Exception as e:
            print(f"❌ Unexpected ping error: {e}")
            time.sleep(300))
        except Exception as e:
            print(f"⚠️ Ping error: {e}")
            time.sleep(300)  # Xatolikda 5 daqiqaga uxlab qolish