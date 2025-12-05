# keep_alive.py - Dynamic port fayli

from flask import Flask
from threading import Thread
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
    # Portni environment variable'dan olish
    port = int(os.getenv('PORT', 10000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )

def start_keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
    port = int(os.getenv('PORT', 10000))
    print(f"✅ Keep-alive server started on port {port}")
    return t