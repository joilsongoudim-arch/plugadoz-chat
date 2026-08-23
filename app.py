from flask import Flask, request, jsonify, session, redirect, send_from_directory, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "plugadoz-secret-change-me")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "plugadoz.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# BANCO DE DADOS
# =========================================================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT DEFAULT '',
            status TEXT DEFAULT '',
            last_seen TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT DEFAULT '',
            file_name TEXT DEFAULT '',
            file_url TEXT DEFAULT '',
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# FUNÇÕES
# =========================================================

def current_user():
    uid = session.get("user_id")

    if not uid:
        return None

    conn = db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (uid,)
    ).fetchone()
    conn.close()

    return user


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# LOGIN
# =========================================================

@app.route("/")
def index():
    if not current_user():
        return redirect("/login")

    return render_template_string(APP_HTML)


@app.route("/login")
def login_page():
    return render_template_string(LOGIN_HTML)


@app.route("/register")
def register_page():
    return render_template_string(REGISTER_HTML)


@app.post("/api/register")
def register():
    data = request.json or {}

    name = data.get("name", "").strip()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if not name or not username or not password:
        return jsonify({
            "ok": False,
            "error": "Preencha todos os campos."
        }), 400

    if len(password) < 4:
        return jsonify({
            "ok": False,
            "error": "A senha precisa ter pelo menos 4 caracteres."
        }), 400

    conn = db()

    exists = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if exists:
        conn.close()
        return jsonify({
            "ok": False,
            "error": "Esse usuário já existe."
        }), 400

    cur = conn.execute("""
        INSERT INTO users
        (name, username, password, last_seen)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        username,
        generate_password_hash(password),
        now()
    ))

    user_id = cur.lastrowid

    conn.commit()
    conn.close()

    session["user_id"] = user_id

    return jsonify({"ok": True})


@app.post("/api/login")
def login():
    data = request.json or {}

    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    conn = db()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if not user or not check_password_hash(user["password"], password):
        conn.close()

        return jsonify({
            "ok": False,
            "error": "Usuário ou senha incorretos."
        }), 401

    conn.execute(
        "UPDATE users SET last_seen = ? WHERE id = ?",
        (now(), user["id"])
    )

    conn.commit()
    conn.close()

    session["user_id"] = user["id"]

    return jsonify({"ok": True})


@app.get("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================================================
# USUÁRIO
# =========================================================

@app.get("/api/me")
def me():
    user = current_user()

    if not user:
        return jsonify({"ok": False}), 401

    conn = db()

    conn.execute(
        "UPDATE users SET last_seen = ? WHERE id = ?",
        (now(), user["id"])
    )

    conn.commit()

    user = conn.execute(
        "SELECT id, name, username, avatar, status, last_seen FROM users WHERE id = ?",
        (user["id"],)
    ).fetchone()

    conn.close()

    return jsonify({
        "ok": True,
        "user": dict(user)
    })


# =========================================================
# PESQUISAR USUÁRIOS
# =========================================================

@app.get("/api/users")
def users():
    user = current_user()

    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    q = request.args.get("q", "").strip()

    conn = db()

    if q:
        rows = conn.execute("""
            SELECT id, name, username, avatar, status, last_seen
            FROM users
            WHERE id != ?
            AND (name LIKE ? OR username LIKE ?)
            ORDER BY name
            LIMIT 50
        """, (
            user["id"],
            f"%{q}%",
            f"%{q}%"
        )).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, name, username, avatar, status, last_seen
            FROM users
            WHERE id != ?
            ORDER BY name
            LIMIT 50
        """, (user["id"],)).fetchall()

    conn.close()

    return jsonify({
        "users": [dict(x) for x in rows]
    })


# =========================================================
# CONVERSAS
# =========================================================

@app.get("/api/chats")
def chats():
    user = current_user()

    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    conn = db()

    rows = conn.execute("""
        SELECT
            u.id,
            u.name,
            u.username,
            u.avatar,
            u.status,
            u.last_seen,
            (
                SELECT text
                FROM messages m
                WHERE
                    (m.sender_id = ? AND m.receiver_id = u.id)
                    OR
                    (m.sender_id = u.id AND m.receiver_id = ?)
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message,
            (
                SELECT created_at
                FROM messages m
                WHERE
                    (m.sender_id = ? AND m.receiver_id = u.id)
                    OR
                    (m.sender_id = u.id AND m.receiver_id = ?)
                ORDER BY m.id DESC
                LIMIT 1
            ) AS message_time
        FROM users u
        WHERE u.id != ?
        AND EXISTS (
            SELECT 1
            FROM messages m
            WHERE
                (m.sender_id = ? AND m.receiver_id = u.id)
                OR
                (m.sender_id = u.id AND m.receiver_id = ?)
        )
        ORDER BY message_time DESC
    """, (
        user["id"],
        user["id"],
        user["id"],
        user["id"],
        user["id"],
        user["id"],
        user["id"]
    )).fetchall()

    conn.close()

    return jsonify({
        "chats": [dict(x) for x in rows]
    })


# =========================================================
# MENSAGENS
# =========================================================

@app.get("/api/messages/<int:user_id>")
def messages(user_id):
    user = current_user()

    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    conn = db()

    rows = conn.execute("""
        SELECT
            m.id,
            m.sender_id,
            m.receiver_id,
            m.text,
            m.file_name,
            m.file_url,
            m.read,
            m.created_at,
            u.name AS sender_name
        FROM messages m
        JOIN users u ON u.id = m.sender_id
        WHERE
            (m.sender_id = ? AND m.receiver_id = ?)
            OR
            (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.id ASC
    """, (
        user["id"],
        user_id,
        user_id,
        user["id"]
    )).fetchall()

    conn.execute("""
        UPDATE messages
        SET read = 1
        WHERE sender_id = ?
        AND receiver_id = ?
    """, (
        user_id,
        user["id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "messages": [dict(x) for x in rows]
    })


@app.post("/api/messages")
def send_message():
    user = current_user()

    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    receiver_id = request.form.get("receiver_id")
    text = request.form.get("text", "").strip()

    if not receiver_id:
        return jsonify({
            "ok": False,
            "error": "Destinatário não informado."
        }), 400

    receiver_id = int(receiver_id)

    file_name = ""
    file_url = ""

    uploaded = request.files.get("file")

    if uploaded and uploaded.filename:
        ext = os.path.splitext(uploaded.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"

        uploaded.save(
            os.path.join(UPLOAD_DIR, filename)
        )

        file_name = uploaded.filename
        file_url = f"/uploads/{filename}"

    if not text and not file_url:
        return jsonify({
            "ok": False,
            "error": "Digite uma mensagem."
        }), 400

    conn = db()

    cur = conn.execute("""
        INSERT INTO messages
        (sender_id, receiver_id, text, file_name, file_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user["id"],
        receiver_id,
        text,
        file_name,
        file_url,
        now()
    ))

    conn.commit()

    message_id = cur.lastrowid

    conn.close()

    return jsonify({
        "ok": True,
        "message_id": message_id
    })


@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# =========================================================
# STATUS
# =========================================================

@app.get("/api/status")
def get_status():
    user = current_user()

    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    conn = db()

    rows = conn.execute("""
        SELECT
            s.id,
            s.text,
            s.created_at,
            u.id AS user_id,
            u.name,
            u.username,
            u.avatar
        FROM statuses s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.id DESC
        LIMIT 100
    """).fetchall()

    conn.close()

    return jsonify({
        "statuses": [dict(x) for x in rows]
    })


@app.post("/api/status")
def create_status():
    user = current_user()

    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    data = request.json or {}

    text = data.get("text", "").strip()

    if not text:
        return jsonify({
            "ok": False,
            "error": "Digite seu status."
        }), 400

    conn = db()

    conn.execute("""
        INSERT INTO statuses
        (user_id, text, created_at)
        VALUES (?, ?, ?)
    """, (
        user["id"],
        text,
        now()
    ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


# =========================================================
# HTML PRINCIPAL
# =========================================================

APP_HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">

<title>Plugadoz</title>

<style>

* {
    box-sizing:border-box;
    margin:0;
    padding:0;
}

body {
    font-family:Arial,Helvetica,sans-serif;
    background:#071017;
    color:#e9edef;
    height:100vh;
    overflow:hidden;
}

button {
    border:0;
    cursor:pointer;
}

.app {
    width:100%;
    height:100vh;
    display:flex;
    flex-direction:column;
    background:#0b141a;
}

.top {
    height:110px;
    background:#202c33;
    flex-shrink:0;
}

.header {
    height:65px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 16px;
}

.logo {
    color:#00a884;
    font-size:23px;
    font-weight:bold;
    letter-spacing:-.5px;
}

.icons {
    display:flex;
    gap:10px;
}

.icon-btn {
    width:43px;
    height:43px;
    border-radius:50%;
    background:transparent;
    color:#d9e1e5;
    display:flex;
    align-items:center;
    justify-content:center;
}

.icon-btn:hover {
    background:#33434c;
}

.icon-btn svg {
    width:23px;
    height:23px;
}

.tabs {
    height:45px;
    display:flex;
}

.tab {
    flex:1;
    color:#8696a0;
    background:transparent;
    font-size:15px;
    font-weight:bold;
    position:relative;
}

.tab.active {
    color:#00a884;
}

.tab.active:after {
    content:"";
    height:3px;
    background:#00a884;
    position:absolute;
    left:0;
    right:0;
    bottom:0;
}

.content {
    flex:1;
    min-height:0;
    position:relative;
}

.page {
    height:100%;
    overflow-y:auto;
}

.chat-list {
    width:100%;
}

.chat {
    height:88px;
    display:flex;
    align-items:center;
    padding:10px 16px;
    border-bottom:1px solid #202c33;
    cursor:pointer;
}

.chat:hover {
    background:#172229;
}

.avatar {
    width:58px;
    height:58px;
    border-radius:50%;
    background:#00a884;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:20px;
    font-weight:bold;
    color:white;
    flex-shrink:0;
}

.chat-info {
    flex:1;
    min-width:0;
    margin-left:14px;
}

.chat-top {
    display:flex;
    justify-content:space-between;
}

.name {
    font-size:16px;
    font-weight:bold;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.time {
    font-size:12px;
    color:#8696a0;
    margin-left:10px;
}

.preview {
    margin-top:6px;
    color:#8696a0;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.empty {
    color:#8696a0;
    text-align:center;
    padding:60px 20px;
}

.status-page {
    padding:15px;
}

.status-create {
    background:#202c33;
    padding:15px;
    border-radius:10px;
    margin-bottom:15px;
}

.status-create input {
    width:100%;
    padding:13px;
    border:0;
    outline:0;
    border-radius:7px;
    background:#111b21;
    color:white;
}

.green-btn {
    margin-top:10px;
    background:#00a884;
    color:white;
    padding:11px 18px;
    border-radius:7px;
    font-weight:bold;
}

.status-card {
    background:#202c33;
    padding:15px;
    border-radius:10px;
    margin-bottom:10px;
}

.status-user {
    font-weight:bold;
    color:#00a884;
}

.status-text {
    margin-top:8px;
}

.chat-window {
    position:absolute;
    inset:0;
    background:#0b141a;
    display:none;
    flex-direction:column;
    z-index:10;
}

.chat-window.open {
    display:flex;
}

.chat-header {
    height:65px;
    background:#202c33;
    display:flex;
    align-items:center;
    padding:0 10px;
    gap:10px;
}

.back {
    color:white;
    background:transparent;
    width:42px;
    height:42px;
}

.chat-title {
    flex:1;
}

.chat-title strong {
    display:block;
}

.chat-title small {
    color:#8696a0;
}

.messages {
    flex:1;
    overflow-y:auto;
    padding:15px;
    background:
        radial-gradient(#18242b 1px, transparent 1px);
    background-size:20px 20px;
}

.message {
    max-width:80%;
    padding:8px 10px;
    margin-bottom:7px;
    border-radius:8px;
    word-wrap:break-word;
}

.message.mine {
    margin-left:auto;
    background:#005c4b;
}

.message.theirs {
    background:#202c33;
}

.message-time {
    display:block;
    font-size:10px;
    color:#aebac1;
    text-align:right;
    margin-top:4px;
}

.composer {
    min-height:62px;
    background:#202c33;
    display:flex;
    align-items:center;
    padding:8px;
    gap:7px;
}

.composer input {
    flex:1;
    background:#111b21;
    border:0;
    outline:none;
    border-radius:20px;
    padding:12px 15px;
    color:white;
    font-size:15px;
}

.send {
    width:45px;
    height:45px;
    border-radius:50%;
    background:#00a884;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
}

.send svg {
    width:21px;
}

.search-box {
    padding:10px;
    background:#111b21;
}

.search-box input {
    width:100%;
    border:0;
    outline:0;
    background:#202c33;
    color:white;
    border-radius:20px;
    padding:12px 17px;
}

.modal {
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.65);
    display:none;
    align-items:flex-end;
    justify-content:center;
    z-index:100;
}

.modal.show {
    display:flex;
}

.modal-box {
    background:#202c33;
    width:100%;
    max-width:500px;
    max-height:80vh;
    border-radius:18px 18px 0 0;
    padding:20px;
    overflow-y:auto;
}

.modal-title {
    font-size:20px;
    font-weight:bold;
    margin-bottom:15px;
}

.user-result {
    display:flex;
    align-items:center;
    padding:12px 0;
    border-bottom:1px solid #334047;
    cursor:pointer;
}

.user-result .avatar {
    width:48px;
    height:48px;
}

.user-result-info {
    margin-left:12px;
}

.close {
    float:right;
    background:transparent;
    color:#8696a0;
    font-size:25px;
}

.file-name {
    color:#b8c7ce;
    font-size:12px;
}

</style>

</head>

<body>

<div class="app">

    <div class="top">

        <div class="header">

            <div class="logo">
                PLUGADOZ
            </div>

            <div class="icons">

                <button class="icon-btn" onclick="openUsers()" title="Nova conversa">

                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="9" cy="8" r="3"/>
                        <path d="M3 20c0-3 2.5-5 6-5s6 2 6 5"/>
                        <path d="M17 8v6"/>
                        <path d="M14 11h6"/>
                    </svg>

                </button>

                <button class="icon-btn" onclick="openUsers()" title="Contatos">

                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="9" cy="8" r="3"/>
                        <circle cx="17" cy="9" r="2"/>
                        <path d="M3 20c0-3 2.5-5 6-5s6 2 6 5"/>
                        <path d="M15 15c3 0 5 2 5 5"/>
                    </svg>

                </button>

            </div>

        </div>

        <div class="tabs">

            <button class="tab active" id="tabChats" onclick="showChats()">
                Conversas
            </button>

            <button class="tab" id="tabStatus" onclick="showStatus()">
                Status
            </button>

        </div>

    </div>


    <div class="content">

        <div id="chatsPage" class="page">

            <div class="search-box">

                <input
                    id="search"
           
