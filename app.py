import os
import base64
import sqlite3
import threading
from datetime import datetime

from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room


# ============================================================
# CONFIGURAÇÃO
# ============================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "plugadoz-secret-key-change-me"
)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    max_http_buffer_size=15 * 1024 * 1024
)

DB_FILE = os.environ.get("DATABASE_PATH", "plugadoz.db")

db_lock = threading.Lock()

online_users = {}
user_sid = {}
typing_users = {}


# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DB_FILE,
        timeout=30,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_lock:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                username TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                last_seen TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS groups_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                owner TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()


init_db()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def display_time(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%H:%M")
    except Exception:
        return value


def save_user(username):
    username = username.strip()[:40]

    if not username:
        return

    with db_lock:
        conn = get_db()

        conn.execute(
            """
            INSERT INTO users(username, last_seen)
            VALUES (?, ?)
            ON CONFLICT(username)
            DO UPDATE SET last_seen=excluded.last_seen
            """,
            (username, now())
        )

        conn.commit()
        conn.close()


def save_message(room, username, msg_type, content):
    created = now()

    with db_lock:
        conn = get_db()

        cur = conn.execute(
            """
            INSERT INTO messages
            (room, username, type, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                room,
                username,
                msg_type,
                content,
                created
            )
        )

        message_id = cur.lastrowid

        conn.commit()
        conn.close()

    return {
        "id": message_id,
        "room": room,
        "username": username,
        "type": msg_type,
        "content": content,
        "time": display_time(created)
    }


def get_messages(room, limit=100):
    with db_lock:
        conn = get_db()

        rows = conn.execute(
            """
            SELECT id, room, username, type, content, created_at
            FROM messages
            WHERE room=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (room, limit)
        ).fetchall()

        conn.close()

    rows = list(reversed(rows))

    result = []

    for row in rows:
        result.append({
            "id": row["id"],
            "room": row["room"],
            "username": row["username"],
            "type": row["type"],
            "content": row["content"],
            "time": display_time(row["created_at"])
        })

    return result


def get_statuses():
    with db_lock:
        conn = get_db()

        rows = conn.execute(
            """
            SELECT id, username, content, created_at
            FROM statuses
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()

        conn.close()

    return [
        {
            "id": row["id"],
            "username": row["username"],
            "content": row["content"],
            "time": display_time(row["created_at"])
        }
        for row in rows
    ]


def create_group(name, owner):
    name = name.strip()[:80]

    if not name:
        return None

    created = now()

    with db_lock:
        conn = get_db()

        try:
            cur = conn.execute(
                """
                INSERT INTO groups_table
                (name, owner, created_at)
                VALUES (?, ?, ?)
                """,
                (name, owner, created)
            )

            group_id = cur.lastrowid
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return None

        conn.close()

    return {
        "id": group_id,
        "name": name,
        "owner": owner,
        "time": display_time(created)
    }


def get_groups():
    with db_lock:
        conn = get_db()

        rows = conn.execute(
            """
            SELECT id, name, owner, created_at
            FROM groups_table
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "owner": row["owner"],
            "time": display_time(row["created_at"])
        }
        for row in rows
    ]


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0,
             maximum-scale=1.0,
             user-scalable=no"
>

<title>Plugadoz</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;
}

html,
body {
    width: 100%;
    height: 100%;
}

body {
    background: #111b21;
    color: #e9edef;
    overflow: hidden;
}


/* =========================================================
   LOGIN
========================================================= */

#login {
    position: fixed;
    inset: 0;
    z-index: 99999;

    background:
        radial-gradient(
            circle at top,
            #173f35 0%,
            #111b21 55%
        );

    display: flex;
    flex-direction: column;

    justify-content: center;
    align-items: center;

    padding: 25px;

    text-align: center;
}

.logo {
    color: #00a884;
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 8px;
}

.subtitle {
    color: #8696a0;
    margin-bottom: 30px;
}

.login-box {
    width: 100%;
    max-width: 360px;
}

#username {
    width: 100%;

    padding: 15px 20px;

    border-radius: 25px;

    border: 1px solid #2a3942;

    background: #202c33;

    color: white;

    outline: none;

    font-size: 16px;

    margin-bottom: 12px;
}

#login-button {
    width: 100%;

    padding: 15px;

    border: none;

    border-radius: 25px;

    background: #00a884;

    color: white;

    font-weight: bold;

    font-size: 16px;

    cursor: pointer;
}


/* =========================================================
   APP
========================================================= */

#app {
    width: 100%;
    height: 100dvh;

    display: flex;

    flex-direction: column;
}

.header {
    height: 62px;

    flex-shrink: 0;

    background: #111b21;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 0 16px;
}

.logo-small {
    color: #00a884;
    font-size: 23px;
    font-weight: 800;
}

.header-icons {
    display: flex;
    gap: 18px;
    align-items: center;

    color: #aebac1;

    font-size: 22px;

    position: relative;
}

.header-icon {
    cursor: pointer;
}


/* =========================================================
   MENU
========================================================= */

#menu-dropdown {
    position: absolute;

    right: 0;
    top: 42px;

    width: 190px;

    background: #233138;

    border-radius: 8px;

    box-shadow:
        0 5px 20px rgba(0,0,0,.5);

    display: none;

    flex-direction: column;

    overflow: hidden;

    z-index: 5000;
}

.menu-item {
    padding: 15px;

    font-size: 14px;

    cursor: pointer;
}

.menu-item:hover {
    background: #182229;
}


/* =========================================================
   FILTERS
========================================================= */

.filters {
    display: flex;

    gap: 8px;

    padding: 8px 14px;

    overflow-x: auto;

    flex-shrink: 0;

    scrollbar-width: none;
}

.filters::-webkit-scrollbar {
    display: none;
}

.filter-chip {
    white-space: nowrap;

    background: #202c33;

    color: #8696a0;

    border-radius: 20px;

    padding: 7px 14px;

    font-size: 13px;

    cursor: pointer;
}

.filter-chip.active {
    background: #005c4b;
    color: #e9edef;
}


/* =========================================================
   CONTENT
========================================================= */

.content-area {
    flex: 1;

    overflow-y: auto;

    min-height: 0;
}

.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
}


/* =========================================================
   CONVERSAS
========================================================= */

.chat-item {
    display: flex;

    align-items: center;

    padding: 11px 15px;

    gap: 13px;

    cursor: pointer;
}

.chat-item:hover {
    background: #202c33;
}

.avatar {
    width: 52px;
    height: 52px;

    border-radius: 50%;

    flex-shrink: 0;

    display: flex;

    align-items: center;
    justify-content: center;

    color: white;

    font-weight: bold;

    font-size: 17px;
}

.chat-info {
    flex: 1;

    min-width: 0;

    padding-bottom: 11px;

    border-bottom: 1px solid #1f2c34;
}

.chat-top {
    display: flex;

    justify-content: space-between;

    gap: 10px;

    margin-bottom: 4px;
}

.chat-name {
    font-size: 16px;

    font-weight: 600;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}

.chat-time {
    color: #8696a0;

    font-size: 11px;

    white-space: nowrap;
}

.chat-msg {
    color: #8696a0;

    font-size: 14px;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}


/* =========================================================
   NAV
========================================================= */

.bottom-nav {
    height: 64px;

    flex-shrink: 0;

    background: #111b21;

    border-top: 1px solid #222d34;

    display: flex;

    align-items: center;

    justify-content: space-around;
}

.nav-item {
    flex: 1;

    height: 100%;

    display: flex;

    flex-direction: column;

    justify-content: center;

    align-items: center;

    gap: 3px;

    color: #8696a0;

    font-size: 11px;

    cursor: pointer;
}

.nav-item span:first-child {
    font-size: 20px;
}

.nav-item.active {
    color: #00a884;
}


/* =========================================================
   CHAT
========================================================= */

#room-screen {
    position: fixed;

    inset: 0;

    z-index: 10000;

    background: #0b141a;

    display: none;

    flex-direction: column;
}

.room-header {
    height: 60px;

    flex-shrink: 0;

    background: #202c33;

    display: flex;

    align-items: center;

    gap: 13px;

    padding: 0 14px;

    border-bottom: 1px solid #222d34;
}

.back {
    font-size: 23px;

    cursor: pointer;
}

.room-info {
    flex: 1;

    min-width: 0;
}

.room-title {
    font-size: 17px;

    font-weight: 600;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;
}

.room-status {
    font-size: 12px;

    color: #8696a0;
}

.room-actions {
    display: flex;

    gap: 16px;

    font-size: 20px;
}

.room-messages {
    flex: 1;

    min-height: 0;

    overflow-y: auto;

    padding: 14px;

    display: flex;

    flex-direction: column;

    gap: 6px;

    background:
        radial-gradient(
            circle at center,
            rgba(20,45,38,.25),
            #0b141a 70%
        );
}

.message-row {
    width: 100%;

    display: flex;
}

.message-row.mine {
    justify-content: flex-end;
}

.bubble {
    max-width: 82%;

    background: #202c33;

    padding: 7px 10px;

    border-radius: 8px;

    box-shadow: 0 1px 1px rgba(0,0,0,.25);

    overflow: hidden;
}

.mine .bubble {
    background: #005c4b;
}

.sender {
    color: #53bdeb;

    font-size: 12px;

    font-weight: 600;

    margin-bottom: 3px;
}

.message-text {
    white-space: pre-wrap;

    word-break: break-word;

    font-size: 15px;

    line-height: 1.35;
}

.message-image {
    display: block;

    max-width: 280px;

    max-height: 350px;

    border-radius: 7px;

    object-fit: contain;

    cursor: pointer;
}

.audio {
    width: 250px;

    max-width: 100%;

    height: 40px;
}

.message-time {
    float: right;

    color: #aebac1;

    font-size: 10px;

    margin-left: 10px;

    margin-top: 5px;
}


/* =========================================================
   TYPING
========================================================= */

#typing {
    display: none;

    padding: 4px 15px;

    color: #00a884;

    font-size: 12px;

    background: #0b141a;
}


/* =========================================================
   FOOTER
========================================================= */

.room-footer {
    min-height: 60px;

    flex-shrink: 0;

    background: #202c33;

    border-top: 1px solid #222d34;

    display: flex;

    align-items: center;

    gap: 7px;

    padding: 8px;
}

.btn-action {
    width: 38px;
    height: 38px;

    border: none;

    background: transparent;

    color: #aebac1;

    font-size: 21px;

    cursor: pointer;
}

.message-input {
    flex: 1;

    min-width: 0;

    border: none;

    outline: none;

    background: #2a3942;

    color: white;

    border-radius: 23px;

    padding: 11px 16px;

    font-size: 15px;
}

.btn-send {
    width: 42px;
    height: 42px;

    flex-shrink: 0;

    border: none;

    border-radius: 50%;

    background: #00a884;

    color: white;

    font-size: 17px;

    cursor: pointer;
}


/* =========================================================
   STATUS
========================================================= */

.status-header {
    padding: 16px;

    color: #8696a0;

    font-size: 13px;

    font-weight: bold;

    text-transform: uppercase;
}

.status-card {
    display: flex;

    gap: 13px;

    padding: 10px 15px;

    cursor: pointer;
}

.status-content {
    flex: 1;

    padding-bottom: 10px;

    border-bottom: 1px solid #1f2c34;
}

.status-text {
    color: #8696a0;

    margin-top: 4px;

    font-size: 14px;
}


/* =========================================================
   EMPTY
========================================================= */

.empty {
    padding: 40px 20px;

    text-align: center;

    color: #8696a0;
}

.empty-icon {
    font-size: 50px;

    margin-bottom: 10px;
}


/* =========================================================
   MODAL
========================================================= */

.modal {
    position: fixed;

    inset: 0;

    z-index: 30000;

    display: none;

    align-items: center;

    justify-content: center;

    background: rgba(0,0,0,.65);

    padding: 20px;
}

.modal-box {
    width: 100%;

    max-width: 380px;

    background: #202c33;

    border-radius: 12px;

    padding: 20px;
}

.modal-title {
    font-size: 19px;

    font-weight: bold;

    margin-bottom: 15px;
}

.modal-input {
    width: 100%;

    padding: 12px;

    background: #2a3942;

    color: white;

    border: none;

    outline: none;

    border-radius: 8px;

    margin-bottom: 15px;
}

.modal-buttons {
    display: flex;

    justify-content: flex-end;

    gap: 10px;
}

.modal-button {
    border: none;

    border-radius: 8px;

    padding: 10px 16px;

    cursor: pointer;
}

.cancel {
    background: #37474f;

    color: white;
}

.confirm {
    background: #00a884;

    color: white;
}


/* =========================================================
   DESKTOP
========================================================= */

@media (min-width: 800px) {

    body {
        background: #0b141a;
    }

    #app {
        width: 500px;

        margin: auto;

        background: #111b21;

        box-shadow:
            0 0 40px rgba(0,0,0,.4);
    }

}

</style>

</head>

<body>


<!-- =======================================================
     LOGIN
======================================================= -->

<div id="login">

    <div class="logo">
        Plugadoz
    </div>

    <div class="subtitle">
        Seu mensageiro conectado
    </div>

    <div class="login-box">

        <input
            id="username"
            type="text"
            maxlength="40"
            placeholder="Digite seu nome"
            autocomplete="off"
        >

        <button
            id="login-button"
            onclick="entrar()"
        >
            Entrar
        </button>

    </div>

</div>


<!-- =======================================================
     APP
======================================================= -->

<div id="app" style="display:none">


    <div class="header">

        <div class="logo-small">
            Plugadoz
        </div>

        <div class="header-icons">

            <span
                class="header-icon"
                onclick="abrirCameraGeral()"
                title="Câmera"
            >
                📷
            </span>

            <span
                class="header-icon"
                onclick="toggleMenu()"
            >
                ⋮
            </span>

            <div id="menu-dropdown">

                <div
                    class="menu-item"
                    onclick="editarPerfil()"
                >
                    👤 Editar perfil
                </div>

                <div
                    class="menu-item"
                    onclick="abrirNovoGrupo()"
                >
                    👥 Novo grupo
                </div>

                <div
                    class="menu-item"
                    onclick="carregarStatus()"
                >
                    🔄 Atualizar
                </div>

                <div
                    class="menu-item"
                    onclick="sobre()"
                >
                    ℹ️ Sobre o Plugadoz
                </div>

                <div
                    class="menu-item"
                    onclick="sair()"
                >
                    🚪 Sair
                </div>

            </div>

        </div>

    </div>


    <!-- FILTROS -->

    <div
        class="filters"
        id="chat-filters"
    >

        <div
            class="filter-chip active"
         
