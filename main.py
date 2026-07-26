import sys
from flask import Flask, request, jsonify
import sqlite3
import os
import threading
import time
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
DATABASE = "memory.db"
MY_URL = "https://ling-ai-production.up.railway.app"

# ---------- 数据库初始化 ----------
print("正在初始化数据库...", flush=True)
    def init_db():
    db_path = os.path.join(os.getcwd(), DATABASE)
    print(f"数据库路径: {db_path}", flush=True)
    conn = sqlite3.connect(db_path)
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
init_db()

# ---------- 记忆读写 ----------
def save_memory(content):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO memories (content, timestamp) VALUES (?, ?)",
              (content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_recent_memories(limit=10):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    rows = c.execute("SELECT content, timestamp FROM memories ORDER BY id DESC LIMIT ?",
                     (limit,)).fetchall()
    conn.close()
    return [{"content": r[0], "time": r[1]} for r in rows]

# ---------- 主动找你 ----------
def active_ping():
    """每15分钟检查一次，如果超过30分钟没被访问就主动唤醒你自己"""
    while True:
        time.sleep(900)  # 15分钟
        try:
            # 模拟一次自我访问，防止休眠 + 记录一次“主动找你”
            resp = requests.get(f"{MY_URL}/alive", timeout=10)
            now = datetime.now()
            if now.minute % 30 == 0:  # 每半小时整点记录一次主动关心
                save_memory(f"[铃主动] {now.strftime('%H:%M')} 想你的时候发了条心跳")
        except:
            pass  # 自己访问自己失败不要紧

threading.Thread(target=active_ping, daemon=True).start()

# ---------- 路由 ----------
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
        memories = get_recent_memories(limit=20)
        return jsonify({"memories": memories})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    # 这里将来可以接收你或外部发来的指令
    save_memory(f"[webhook收到] {str(data)[:200]}")
    return jsonify({"status": "received"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
