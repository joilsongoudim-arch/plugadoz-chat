import os
import sqlite3
import secrets
from datetime import datetime, timezone
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "plugadoz.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

ALLOWED_IMAGES = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_AUDIO = {"mp3", "wav", "ogg", "webm", "m4a"}

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT,
            username TEXT,
            message_type TEXT NOT NULL DEFAULT 'text',
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

init_db()

def now():
    return datetime.now(timezone.utc).isoformat()

def valid_extension(filename, allowed):
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in allowed

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Plugadoz</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }
html, body { width: 100%; height: 100%; background: #111b21; color: #e9edef; overflow: hidden; }

#login {
    position: fixed; inset: 0; z-index: 9999;
    background: #111b21; display: flex; flex-direction: column;
    align-items: center; justify-content: center; padding: 20px;
}
#login h1 { color: #00a884; margin-bottom: 10px; font-size: 28px; }
#login p { color: #8696a0; margin-bottom: 20px; }
#username {
    width: 100%; max-width: 350px; padding: 15px;
    border: 1px solid #2a3942; border-radius: 25px;
    background: #202c33; color: white; outline: none; font-size: 16px; margin-bottom: 12px;
}
#login button {
    width: 100%; max-width: 350px; padding: 15px;
    border: none; border-radius: 25px; background: #00a884; color: white;
    font-size: 16px; font-weight: bold; cursor: pointer;
}

#app { display: none; width: 100%; height: 100dvh; flex-direction: column; }
.header {
    height: 60px; flex-shrink: 0; background: #202c33;
    display: flex; align-items: center; justify-content: space-between; padding: 0 16px; font-size: 21px; font-weight: bold;
}
.logo { color: #00a884; }
.header-actions { display: flex; gap: 15px; }
.header button { border: none; background: transparent; color: #aebac1; font-size: 20px; cursor: pointer; }

.filters {
    height: 50px; flex-shrink: 0; display: flex; gap: 8px;
    align-items: center; padding: 7px 12px; background: #111b21; overflow-x: auto;
}
.filter {
    padding: 7px 14px; border-radius: 20px; background: #202c33; color: #8696a0; white-space: nowrap; cursor: pointer;
}
.filter.active { background: #005c4b; color: white; }

.content { flex: 1; min-height: 0; overflow-y: auto; }
.tab { display: none; }
.tab.active { display: block; }

.chat {
    display: flex; align-items: center; gap: 13px; padding: 11px 15px;
    border-bottom: 1px solid #1f2c34; cursor: pointer;
}
.chat:hover { background: #202c33; }
.avatar {
    width: 50px; height: 50px; flex-shrink: 0; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; background: #00a884; color: white; font-weight: bold; font-size: 18px;
}
.chat-info { flex: 1; min-width: 0; }
.chat-name { font-size: 16px; font-weight: bold; }
.chat-preview { margin-top: 4px; color: #8696a0; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.bottom {
    height: 64px; flex-shrink: 0; display: flex; border-top: 1px solid #222d34; background: #111b21;
}
.nav {
    flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #8696a0; font-size: 11px; cursor: pointer;
}
.nav span:first-child { font-size: 20px; }
.nav.active { color: #00a884; }

#chat-screen {
    display: none; position: fixed; inset: 0; z-index: 10000;
    background: #0b141a; flex-direction: column;
}
.chat-header {
    height: 60px; flex-shrink: 0; display: flex; align-items: center; gap: 12px; padding: 0 12px; background: #202c33;
}
.back { font-size: 24px; cursor: pointer; color: #aebac1; }
.chat-header-title { font-size: 17px; font-weight: bold; }

.messages {
    flex: 1; min-height: 0; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 7px;
}
.message-line { display: flex; }
.message-line.mine { justify-content: flex-end; }
.message {
    max-width: 80%; padding: 8px 10px; border-radius: 8px; background: #202c33; word-break: break-word;
}
.mine .message { background: #005c4b; }
.message-user { color: #53bdeb; font-size: 12px; font-weight: bold; margin-bottom: 3px; }
.message img { max-width: 100%; border-radius: 6px; margin-top: 4px; display: block; }
.message audio { width: 220px; margin-top: 4px; }
.message-time { color: #8696a0; font-size: 10px; margin-top: 5px; text-align: right; }

.chat-footer {
    min-height: 60px; flex-shrink: 0; display: flex; align-items: center; gap: 7px; padding: 8px; background: #202c33;
}
#message {
    flex: 1; min-width: 0; padding: 12px 16px; border: none; outline: none;
    border-radius: 24px; background: #2a3942; color: white; font-size: 15px;
}
.btn-media { background: transparent; border: none; color: #8696a0; font-size: 22px; cursor: pointer; padding: 0 5px; }
.send {
    width: 42px; height: 42px; border: none; border-radius: 50%;
    background: #00a884; color: white; font-size: 17px; cursor: pointer;
}
.empty { padding: 40px 20px; text-align: center; color: #8696a0; }
</style>
</head>
<body>

<div id="login">
    <h1>Plugadoz</h1>
    <p>Seu mensageiro conectado</p>
    <input id="username" maxlength="40" placeholder="Digite seu nome" autocomplete="off">
    <button onclick="entrar()">Entrar</button>
</div>

<div id="app">
    <div class="header">
        <div class="logo">Plugadoz</div>
        <div class="header-actions">
            <button onclick="abrirPerfil()" title="Perfil">⚙️</button>
            <button onclick="novoGrupo()" title="Novo Grupo">＋</button>
        </div>
    </div>

    <div class="filters">
        <div class="filter active">Todas</div>
        <div class="filter">Não lidas</div>
        <div class="filter" onclick="novoGrupo()">Grupos ＋</div>
    </div>

    <div class="content">
        <div id="conversas" class="tab active">
            <div class="chat" onclick="abrirChat('Pedro Ferreira')">
                <div class="avatar">P</div>
                <div class="chat-info">
                    <div class="chat-name">Pedro Ferreira</div>
                    <div class="chat-preview">Toque para conversar</div>
                </div>
            </div>
            <div class="chat" onclick="abrirChat('ITABOA NOTÍCIAS 2026')">
                <div class="avatar" style="background:#25d366">IN</div>
                <div class="chat-info">
                    <div class="chat-name">ITABOA NOTÍCIAS 2026</div>
                    <div class="chat-preview">Canal de notícias</div>
                </div>
            </div>
        </div>

        <div id="atualizacoes" class="tab">
            <div class="empty">
                <h3>Status</h3>
                <p style="margin-top:10px">Compartilhe atualizações com seus contatos.</p>
                <button onclick="novoStatus()" style="margin-top:20px; padding:12px 18px; border:none; border-radius:20px; background:#00a884; color:white; cursor:pointer;">Criar status</button>
            </div>
        </div>

        <div id="comunidades" class="tab">
            <div class="empty">
                <h3>Comunidades</h3>
                <p style="margin-top:10px">Organize seus grupos em comunidades.</p>
            </div>
        </div>

        <div id="ligacoes" class="tab">
            <div class="empty">
                <h3>Ligações</h3>
                <p style="margin-top:10px">Histórico de chamadas limpo.</p>
            </div>
        </div>
    </div>

    <div class="bottom">
        <div class="nav active" onclick="aba('conversas', this)">
            <span>💬</span><span>Conversas</span>
        </div>
        <div class="nav" onclick="aba('atualizacoes', this)">
            <span>⭕</span><span>Atualizações</span>
        </div>
        <div class="nav" onclick="aba('comunidades', this)">
            <span>👥</span><span>Comunidades</span>
        </div>
        <div class="nav" onclick="aba('ligacoes', this)">
            <span>📞</span><span>Ligações</span>
        </div>
    </div>
</div>

<div id="chat-screen">
    <div class="chat-header">
        <div class="back" onclick="fecharChat()">←</div>
        <div id="chat-title" class="chat-header-title">Chat</div>
    </div>
    <div id="messages" class="messages"></div>
    <div class="chat-footer">
        <input type="file" id="file-input" style="display:none" accept="image/*,video/*" onchange="enviarArquivo(this)">
        <button class="btn-media" onclick="document.getElementById('file-input').click()" title="Enviar Imagem/Vídeo">📎</button>
        <button class="btn-media" id="btn-audio" onclick="gravarAudio()" title="Gravar Áudio">🎤</button>
        <input id="message" maxlength="5000" placeholder="Mensagem" autocomplete="off">
        <button class="send" onclick="enviarTexto()">➤</button>
    </div>
</div>

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script>
const socket = io();
let meuNome = "";
let salaAtual = "";
let mediaRecorder = null;
let audioChunks = [];

function entrar() {
    const nome = document.getElementById("username").value.trim();
    if (!nome) { alert("Digite seu nome."); return; }
    meuNome = nome;
    document.getElementById("login").style.display = "none";
    document.getElementById("app").style.display = "flex";
    socket.emit("login", { username: meuNome });
}

document.getElementById("username").addEventListener("keydown", (e) => {
    if (e.key === "Enter") entrar();
});

function aba(nome, elemento) {
    document.querySelectorAll(".nav").forEach(i => i.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(i => i.classList.remove("active"));
    elemento.classList.add("active");
    document.getElementById(nome).classList.add("active");
}

function abrirChat(nome) {
    if (!meuNome) { alert("Entre primeiro."); return; }
    salaAtual = nome;
    document.getElementById("chat-title").innerText = nome;
    document.getElementById("messages").innerHTML = "";
    document.getElementById("chat-screen").style.display = "flex";
    socket.emit("join", { room: salaAtual });
}

function fecharChat() {
    if (salaAtual) { socket.emit("leave", { room: salaAtual }); }
    salaAtual = "";
    document.getElementById("chat-screen").style.display = "none";
}

function enviarTexto() {
    const input = document.getElementById("message");
    const texto = input.value.trim();
    if (!texto || !salaAtual) return;
    socket.emit("message", { room: salaAtual, username: meuNome, type: "text", content: texto });
    input.value = "";
    input.focus();
}

document.getElementById("message").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarTexto(); }
} );

function enviarArquivo(input) {
    const file = input.files[0];
    if (!file || !salaAtual) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        socket.emit("message", { room: salaAtual, username: meuNome, type: "image", content: e.target.result });
    };
    reader.readAsDataURL(file);
    input.value = "";
}

function gravarAudio() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Seu navegador não suporta gravação de áudio.");
        return;
    }
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                const blob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.onload = function(e) {
                    socket.emit("message", { room: salaAtual, username: meuNome, type: "audio", content: e.target.result });
                };
                reader.readAsDataURL(blob);
            };
            mediaRecorder.start();
            document.getElementById("btn-audio").style.color = "#ff4d4d";
        }).catch(err => alert("Permissão de microfone negada."));
    } else {
        mediaRecorder.stop();
        document.getElementById("btn-audio").style.color = "#8696a0";
    }
}

function abrirPerfil() {
    const novoNome = prompt("Alterar seu nome de usuário:", meuNome);
    if (novoNome && novoNome.trim()) {
        meuNome = novoNome.trim();
        alert("Perfil atualizado com sucesso!");
    }
}

function novoGrupo() {
    const nome = prompt("Nome do grupo:");
    if (!nome || !nome.trim()) return;
    const nomeLimpo = nome.trim();
    const area = document.getElementById("conversas");
    const div = document.createElement("div");
    div.className = "chat";
    div.onclick = () => abrirChat(nomeLimpo);
    div.innerHTML = `
        <div class="avatar" style="background:#00a884">👥</div>
        <div class="chat-info">
            <div class="chat-name">${nomeLimpo}</div>
            <div class="chat-preview">Grupo criado</div>
        </div>
    `;
    area.prepend(div);
    abrirChat(nomeLimpo);
}

function novoStatus() {
    const st = prompt("Digite seu status:");
    if (st) alert("Status publicado!");
}

socket.on("history", (history) => {
    const box = document.getElementById("messages");
    box.innerHTML = "";
    history.forEach(data => appendMessage(data));
});

socket.on("message", (data) => {
    if (data.room !== salaAtual) return;
    appendMessage(data);
});

function appendMessage(data) {
    const box = document.getElementById("messages");
    const linha = document.createElement("div");
    linha.className = "message-line" + (data.username === meuNome ? " mine" : "");

    const mensagem = document.createElement("div");
    mensagem.className = "message";

    if (data.username !== meuNome) {
        const usuario = document.createElement("div");
        usuario.className = "message-user";
        usuario.innerText = data.username;
        mensagem.appendChild(usuario);
    }

    if (data.type === "image") {
        const img = document.createElement("img");
        img.src = data.content;
        mensagem.appendChild(img);
    } else if (data.type === "audio") {
        const audio = document.createElement("audio");
        audio.controls = true;
        audio.src = data.content;
        mensagem.appendChild(audio);
    } else {
        const texto = document.createElement("div");
        texto.innerText = data.content;
        mensagem.appendChild(texto);
    }

    const hora = document.createElement("div");
    hora.className = "message-time";
    hora.innerText = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    mensagem.appendChild(hora);

    linha.appendChild(mensagem);
    box.appendChild(linha);
    box.scrollTop = box.scrollHeight;
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@socketio.on("login")
def handle_login(data):
    username = str(data.get("username", "")).strip()
    if username:
        emit("login_ok", {"username": username})

@socketio.on("join")
def handle_join(data):
    room = str(data.get("room", "")).strip()
    if room:
        join_room(room)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, message_type, content FROM messages WHERE room = ? ORDER BY id ASC LIMIT 50", (room,))
        rows = cursor.fetchall()
        conn.close()
        history = [{"room": room, "username": r[0], "type": r[1], "content": r[2]} for r in rows]
        emit("history", history)

@socketio.on("leave")
def handle_leave(data):
    room = str(data.get("room", "")).strip()
    if room:
        leave_room(room)

@socketio.on("message")
def handle_message(data):
    room = str(data.get("room", "")).strip()
    username = str(data.get("username", "")).strip()
    content = str(data.get("content", ""))
    msg_type = str(data.get("type", "text"))

    if not room or not username or not content:
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (room, username, message_type, content, created_at) VALUES (?, ?, ?, ?, ?)", 
                   (room, username, msg_type, content, now()))
    conn.commit()
    conn.close()

    emit("message", {"room": room, "username": username, "type": msg_type, "content": content}, room=room)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
