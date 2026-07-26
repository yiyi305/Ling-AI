from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "铃 在线"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    return jsonify({"status": "received", "message": data})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
