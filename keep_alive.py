# keep_alive.py - FINAL WORKING VERSION

from flask import Flask
from threading import Thread

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
    return t