from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import sqlite3

app = Flask(__name__, static_folder='.')
CORS(app)

DB_FILE = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            text TEXT,
            time TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            text TEXT,
            time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/chat', methods=['GET'])
def get_chat():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT sender, text, time FROM mensagens ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    
    mensagens = [{"sender": r[0], "text": r[1], "time": r[2]} for r in rows]
    return jsonify(mensagens)

@app.route('/api/chat', methods=['POST'])
def post_chat():
    data = request.get_json()
    if not data or not data.get('text') or not data.get('sender'):
        return jsonify({"error": "dados inválidos"}), 400
    
    sender = str(data.get('sender'))[:50]
    text = str(data.get('text'))[:1000]
    time_str = data.get('time') or datetime.now().strftime('%H:%M')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO mensagens (sender, text, time) VALUES (?, ?, ?)', (sender, text, time_str))
    conn.commit()
    conn.close()
    
    return jsonify({"ok": True})

@app.route('/api/status', methods=['GET','POST'])
def handle_status():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT sender, text, time FROM status ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        status_list = [{"sender": r[0], "text": r[1], "time": r[2]} for r in rows]
        return jsonify(status_list)
        
    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({"error": "dados inválidos"}), 400
        
    sender = str(data.get('sender'))[:50]
    text = str(data.get('text'))[:1000]
    time_str = datetime.now().strftime('%H:%M')

    cursor.execute('INSERT INTO status (sender, text, time) VALUES (?, ?, ?)', (sender, text, time_str))
    conn.commit()
    conn.close()
    
    return jsonify({"ok": True})

@app.route('/health')
def health():
    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
        
