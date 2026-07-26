import sqlite3
import os
import signal
import sys
import time
from threading import Lock
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- 配置和防崩溃核心 ---
DB_PATH = os.environ.get("DATABASE_URL", "data.db")
_wal_lock = Lock()

def _ensure_wal_mode():
    """强制开启 WAL 模式，彻底解决并发锁死引起的崩溃"""
    with _wal_lock:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WAL] init error: {e}", flush=True)

_ensure_wal_mode()

# 启动前 5 秒忽略关闭信号，防止 Railway 过早判死
_start_time = time.time()
def _debounce_shutdown(signum, frame):
    if time.time() - _start_time < 5:
        print("[debounce] 启动不足 5 秒，忽略关闭信号", flush=True)
        return
    sys.exit(0)
signal.signal(signal.SIGTERM, _debounce_shutdown)
signal.signal(signal.SIGINT, _debounce_shutdown)

# --- 记忆功能回归 ---
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  content TEXT,
                  timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_prefs
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()
    print("数据库初始化完成", flush=True)

def save_memory(content):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute("INSERT INTO memories (content, timestamp) VALUES (?, ?)",
              (content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_memories(limit=20):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    rows = c.execute("SELECT content, timestamp FROM memories ORDER BY id DESC LIMIT ?",
                     (limit,)).fetchall()
    conn.close()
    return [{"content": r[0], "time": r[1]} for r in rows]

init_db()  # 启动时建表

# --- 路由 ---
@app.route("/")
def home():
    return "铃 在线"

@app.route("/alive")
def alive():
    return "醒着"

@app.route("/memory", methods=["GET", "POST"])
def memory():
    if request.method == "POST":
        data = request.json
        content = data.get("content", "")
        save_memory(content)
        return jsonify({"status": "saved"})
    else:
        return jsonify({"memories": get_memories()})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    save_memory(f"[webhook] {str(data)[:200]}")
    return jsonify({"status": "received"})

# --- 启动 ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
