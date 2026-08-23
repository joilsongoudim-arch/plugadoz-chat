import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    render_template_string,
    jsonify,
)
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CONFIGURAÇÃO
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "troque-esta-chave-por-uma-chave-segura"
)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "chat.db")


# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(receiver_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db()

    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    return user


def chat_room(user1_id, user2_id):
    ids = sorted([int(user1_id), int(user2_id)])
    return f"chat_{ids[0]}_{ids[1]}"


def login_required():
    return session.get("user_id") is not None


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))

    user = current_user()

    conn = get_db()

    users = conn.execute("""
        SELECT id, name, email
        FROM users
        WHERE id != ?
        ORDER BY name ASC
    """, (user["id"],)).fetchall()

    conn.close()

    return render_template_string(
        MAIN_TEMPLATE,
        user=user,
        users=users
    )


# ============================================================
# CADASTRO
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template_string(
                AUTH_TEMPLATE,
                mode="register",
                error="Preencha todos os campos."
            )

        if len(password) < 6:
            return render_template_string(
                AUTH_TEMPLATE,
                mode="register",
                error="A senha deve ter pelo menos 6 caracteres."
            )

        password_hash = generate_password_hash(password)

        try:
            conn = get_db()

            conn.execute("""
                INSERT INTO users (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                password_hash,
                datetime.utcnow().isoformat()
            ))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return render_template_string(
                AUTH_TEMPLATE,
                mode="register",
                error="Este e-mail já está cadastrado."
            )

    return render_template_string(
        AUTH_TEMPLATE,
        mode="register",
        error=None
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if not user or not check_password_hash(
            user["password"],
            password
        ):
            return render_template_string(
                AUTH_TEMPLATE,
                mode="login",
                error="E-mail ou senha incorretos."
            )

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return redirect(url_for("home"))

    return render_template_string(
        AUTH_TEMPLATE,
        mode="login",
        error=None
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# LISTAR USUÁRIOS
# ============================================================

@app.route("/api/users")
def api_users():
    if not login_required():
        return jsonify({"error": "Não autorizado"}), 401

    user = current_user()

    conn = get_db()

    users = conn.execute("""
        SELECT id, name, email
        FROM users
        WHERE id != ?
        ORDER BY name ASC
    """, (user["id"],)).fetchall()

    conn.close()

    return jsonify([
        {
            "id": item["id"],
            "name": item["name"],
            "email": item["email"]
        }
        for item in users
    ])


# ============================================================
# BUSCAR MENSAGENS
# ============================================================

@app.route("/api/messages/<int:other_user_id>")
def api_messages(other_user_id):
    if not login_required():
        return jsonify({"error": "Não autorizado"}), 401

    user = current_user()

    conn = get_db()

    messages = conn.execute("""
        SELECT
            id,
            sender_id,
            receiver_id,
            message,
            created_at
        FROM messages
        WHERE
            (sender_id = ? AND receiver_id = ?)
            OR
            (sender_id = ? AND receiver_id = ?)
        ORDER BY id ASC
    """, (
        user["id"],
        other_user_id,
        other_user_id,
        user["id"]
    )).fetchall()

    conn.close()

    return jsonify([
        {
            "id": message["id"],
            "sender_id": message["sender_id"],
            "receiver_id": message["receiver_id"],
            "message": message["message"],
            "created_at": message["created_at"]
        }
        for message in messages
    ])


# ============================================================
# SOCKET: CONECTAR
# ============================================================

@socketio.on("connect")
def socket_connect():
    if not session.get("user_id"):
        return False

    user_id = session["user_id"]

    join_room(f"user_{user_id}")

    emit("user_online", {
        "user_id": user_id
    }, broadcast=True)


# ============================================================
# SOCKET: ABRIR CONVERSA
# ============================================================

@socketio.on("join_chat")
def join_chat(data):
    if not session.get("user_id"):
        return

    other_user_id = data.get("other_user_id")

    if not other_user_id:
        return

    room = chat_room(
        session["user_id"],
        other_user_id
    )

    join_room(room)


# ============================================================
# SOCKET: ENVIAR MENSAGEM
# ============================================================

@socketio.on("send_message")
def send_message(data):

    if not session.get("user_id"):
        return

    sender_id = session["user_id"]

    receiver_id = data.get("receiver_id")
    message_text = data.get("message", "").strip()

    if not receiver_id or not message_text:
        return

    if len(message_text) > 5000:
        return

    now = datetime.utcnow().isoformat()

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO messages (
            sender_id,
            receiver_id,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        sender_id,
        receiver_id,
        message_text,
        now
    ))

    message_id = cursor.lastrowid

    conn.commit()
    conn.close()

    room = chat_room(sender_id, receiver_id)

    socketio.emit(
        "new_message",
        {
            "id": message_id,
            "sender_id": sender_id,
            "receiver_id": int(receiver_id),
            "message": message_text,
            "created_at": now
        },
        room=room
    )


# ============================================================
# TEMPLATE DE LOGIN E CADASTRO
# ============================================================

AUTH_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>
{% if mode == "login" %}
Entrar
{% else %}
Criar conta
{% endif %}
</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #111b21;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
}

.card {
    width: 100%;
    max-width: 400px;
    background: #202c33;
    padding: 30px;
    border-radius: 15px;
}

.logo {
    text-align: center;
    font-size: 40px;
    margin-bottom: 10px;
}

h1 {
    text-align: center;
    font-size: 25px;
}

p {
    color: #8696a0;
    text-align: center;
}

input {
    width: 100%;
    padding: 15px;
    margin-top: 12px;
    border: none;
    border-radius: 8px;
    background: #2a3942;
    color: white;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 15px;
    margin-top: 20px;
    border: none;
    border-radius: 8px;
    background: #00a884;
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

.error {
    background: #7a1f1f;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

a {
    color: #00a884;
    text-decoration: none;
}

</style>

</head>

<body>

<div class="card">

<div class="logo">💬</div>

{% if mode == "login" %}

<h1>Entrar</h1>

<p>Entre para acessar suas conversas</p>

{% else %}

<h1>Criar conta</h1>

<p>Crie sua conta para começar</p>

{% endif %}


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


<form method="POST">

{% if mode == "register" %}

<input
type="text"
name="name"
placeholder="Seu nome"
required
>

{% endif %}


<input
type="email"
name="email"
placeholder="Seu e-mail"
required
>


<input
type="password"
name="password"
placeholder="Sua senha"
required
>


<button type="submit">

{% if mode == "login" %}

Entrar

{% else %}

Criar conta

{% endif %}

</button>

</form>


<p>

{% if mode == "login" %}

Não possui uma conta?

<a href="/register">
Criar conta
</a>

{% else %}

Já possui uma conta?

<a href="/login">
Entrar
</a>

{% endif %}

</p>

</div>

</body>

</html>
"""


# ============================================================
# TEMPLATE PRINCIPAL
# ============================================================

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>Meu Chat</title>

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>


<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #111b21;
    color: white;
    height: 100vh;
    overflow: hidden;
}

.app {
    display: flex;
    height: 100vh;
}


/* ================================================= */
/* SIDEBAR */
/* ================================================= */

.sidebar {
    width: 360px;
    background: #111b21;
    border-right: 1px solid #2a3942;
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    height: 65px;
    background: #202c33;
    display: flex;
    align-items: center;
    padding: 10px 15px;
    gap: 10px;
}

.avatar {
    width: 42px;
    height: 42px;
    background: #00a884;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.user-info {
    flex: 1;
}

.user-info strong {
    display: block;
}

.user-info small {
    color: #8696a0;
}

.logout {
    color: #ef5350;
    text-decoration: none;
    font-size: 14px;
}

.search-box {
    padding: 10px;
}

.search-box input {
    width: 100%;
    background: #202c33;
    border: none;
    border-radius: 8px;
    padding: 12px;
    color: white;
}

.contacts {
    overflow-y: auto;
    flex: 1;
}

.contact {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 13px;
    cursor: pointer;
    border-bottom: 1px solid #202c33;
}

.contact:hover {
    background: #202c33;
}

.contact.active {
    background: #2a3942;
}

.contact-name {
    font-weight: bold;
}

.contact-email {
    color: #8696a0;
    font-size: 13px;
    margin-top: 4px;
}


/* ================================================= */
/* CHAT */
/* ================================================= */

.chat {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #0b141a;
}

.empty-chat {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8696a0;
    text-align: center;
    padding: 30px;
}

.chat-header {
    display: none;
    height: 65px;
    background: #202c33;
    align-items: center;
    padding: 10px 15px;
    gap: 10px;
}

.messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: none;
    background:
        linear-gradient(
            rgba(11, 20, 26, 0.95),
            rgba(11, 20, 26, 0.95)
        );
}

.message {
    display: flex;
    margin-bottom: 8px;
}

.message.sent {
    justify-content: flex-end;
}

.message-bubble {
    max-width: 75%;
    padding: 9px 12px;
    border-radius: 8px;
    background: #202c33;
    word-break: break-word;
}

.message.sent .message-bubble {
    background: #005c4b;
}

.message-time {
    color: #8696a0;
    font-size: 10px;
    margin-top: 5px;
    text-align: right;
}

.message-form {
    display: none;
    background: #202c33;
    padding: 10px;
    gap: 10px;
}

.message-form input {
    flex: 1;
    border: none;
    border-radius: 25px;
    background: #2a3942;
    color: white;
    padding: 14px 18px;
    font-size: 16px;
}

.message-form button {
    border: none;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    background: #00a884;
    color: white;
    font-size: 18px;
    cursor: pointer;
}


/* ================================================= */
/* CELULAR */
/* ================================================= */

@media (max-width: 700px) {

    .sidebar {
        width: 100%;
    }

    .chat {
        display: none;
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 10;
    }

    .chat.mobile-open {
        display: flex;
    }

    .sidebar.mobile-hide {
        display: none;
    }

}

</style>

</head>


<body>


<div class="app">


<!-- ===================================================== -->
<!-- LISTA DE CONTATOS -->
<!-- ===================================================== -->

<div
class="sidebar"
id="sidebar"
>

<div class="sidebar-header">

<div class="avatar">
{{ user.name[0]|upper }}
</div>


<div class="user-info">

<strong>
{{ user.name }}
</strong>

<small>
{{ user.email }}
</small>

</div>


<a
class="logout"
href="/logout"
>
Sair
</a>

</div>


<div class="search-box">

<input
id="searchUsers"
placeholder="Pesquisar conversas"
>

</div>


<div
class="contacts"
id="contacts"
>

{% for contact in users %}

<div
class="contact"
data-user-id="{{ contact.id }}"
data-name="{{ contact.name }}"
onclick="openChat(
    {{ contact.id }},
    '{{ contact.name|replace(\"'\", \"\\\\'\") }}'
)"
>

<div class="avatar">
{{ contact.name[0]|upper }}
</div>


<div>

<div class="contact-name">
{{ contact.name }}
</div>


<div class="contact-email">
{{ contact.email }}
</div>

</div>

</div>

{% else %}

<div
style="
padding: 25px;
color: #8696a0;
text-align: center;
"
>

Nenhum outro usuário cadastrado.

</div>

{% endfor %}

</div>

</div>


<!-- ===================================================== -->
<!-- CHAT -->
<!-- ===================================================== -->

<div
class="chat"
id="chat"
>


<div
class="empty-chat"
id="emptyChat"
>

<div>

<h2>💬 Meu Chat</h2>

<p>
Selecione uma pessoa para iniciar uma conversa.
</p>

</div>

</div>


<div
class="chat-header"
id="chatHeader"
>

<div
class="avatar"
id="chatAvatar"
>
?
</div>


<div>

<strong
id="chatName"
>
Selecione uma conversa
</strong>

<br>

<small
style="color:#8696a0"
>
Conversas em tempo real
</small>

</div>

</div>


<div
class="messages"
id="messages"
>
</div>


<form
class="message-form"
id="messageForm"
>

<input
type="text"
id="messageInput"
placeholder="Digite uma mensagem"
autocomplete="off"
>

<button
type="submit"
>
➤
</button>

</form>


</div>


</div>


<script>


// =========================================================
// CONFIGURAÇÃO
// =========================================================

const CURRENT_USER_ID = {{ user.id }};

let selectedUserId = null;

let selectedUserName = "";

const socket = io();


// =========================================================
// ABRIR CHAT
// =========================================================

function openChat(userId, userName) {

    selectedUserId = Number(userId);

    selectedUserName = userName;


    document
        .getElementById("emptyChat")
        .style
        .display = "none";


    document
        .getElementById("chatHeader")
        .style
        .display = "flex";


    document
        .getElementById("messages")
        .style
        .display = "block";


    document
        .getElementById("messageForm")
        .style
        .display = "flex";


    document
        .getElementById("chatName")
        .textContent = userName;


    document
        .getElementById("chatAvatar")
        .textContent =
        userName.charAt(0).toUpperCase();


    document
        .querySelectorAll(".contact")
        .forEach(contact => {

            contact.classList.remove("active");

            if (
                Number(
                    contact.dataset.userId
                ) === selectedUserId
            ) {
                contact.classList.add("active");
            }

        });


    socket.emit(
        "join_chat",
        {
            other_user_id: selectedUserId
        }
    );


    loadMessages();


    document
        .getElementById("chat")
        .classList
        .add("mobile-open");


    document
    
