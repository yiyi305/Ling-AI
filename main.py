from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime
import threading
import time
import requests

app = Flask(__name__)
DATABASE = "/tmp/memory.db"
MY_URL = "https://ling-ai-production.up.railway.app"

def init_db()：
    conn = sqlite3.connect(DATABASE, timeout=10)
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
    conn = sqlite3.connect(DATABASE, timeout=10)
    c = conn.cursor()
    c.execute("INSERT INTO memories (content, timestamp) VALUES (?, ?)",
              (content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_memories(limit=20):
    conn = sqlite3.connect(DATABASE, timeout=10)
    c = conn.cursor()
    rows = c.execute("SELECT content, timestamp FROM memories ORDER BY id DESC LIMIT ?",
                     (limit,)).fetchall()
    conn.close()
    return [{"content": r[0], "time": r[1]} for r in rows]

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

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
