import os
import sqlite3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "plugadoz.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "plugadoz-whatsapp-key"
socketio = SocketIO(app, cors_allowed_origins="*")

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join")
def on_join(data):
    room = data["room"]
    join_room(room)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, type, content FROM messages WHERE room = ? ORDER BY id ASC", (room,))
    rows = cursor.fetchall()
    conn.close()
    emit("history", [{"username": r[0], "type": r[1], "content": r[2]} for r in rows])

@socketio.on("leave")
def on_leave(data):
    leave_room(data["room"])

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    username = data["username"]
    msg_type = data["type"]
    content = data["content"]
    
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT INTO messages (room, username, type, content) VALUES (?, ?, ?, ?)",
                 (room, username, msg_type, content))
    conn.commit()
    conn.close()
    
    emit("message", {"room": room, "username": username, "type": msg_type, "content": content}, to=room)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
    
