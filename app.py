import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-whatsapp-key'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WhatsApp</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #111b21; color: #e9edef; height: 100vh; height: 100dvh; display: flex; flex-direction: column; overflow: hidden; }
        
        #login { position: fixed; inset: 0; background: #111b21; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; padding: 20px; text-align: center; }
        #login input { width: 100%; max-width: 320px; padding: 14px 20px; border-radius: 24px; border: 1px solid #222d34; background: #202c33; color: #fff; font-size: 16px; margin-bottom: 16px; text-align: center; outline: none; }
        #login button { width: 100%; max-width: 320px; padding: 14px; border-radius: 24px; border: none; background: #00a884; color: white; font-size: 16px; font-weight: bold; cursor: pointer; }
        
        .header { background: #202c33; padding: 14px 16px; font-size: 20px; font-weight: bold; color: #00a884; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222d34; flex-shrink: 0; }
        .nav-tabs { display: flex; background: #202c33; border-bottom: 1px solid #222d34; flex-shrink: 0; }
        .nav-tab { flex: 1; text-align: center; padding: 12px; color: #8696a0; font-weight: 600; font-size: 15px; cursor: pointer; border-bottom: 3px solid transparent; }
        .nav-tab.active { color: #00a884; border-bottom-color: #00a884; }

        .tab-content { flex: 1; overflow-y: auto; background: #111b21; display: none; }
        .tab-content.active { display: block; }

        .chat-item { display: flex; align-items: center; padding: 12px 16px; gap: 14px; cursor: pointer; border-bottom: 1px solid #1f2c34; }
        .chat-item:active { background: #202c33; }
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; flex-shrink: 0; font-size: 16px; }
        .chat-info { flex: 1; min-width: 0; }
        .chat-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .chat-name { font-size: 16px; font-weight: 600; color: #e9edef; }
        .chat-time { font-size: 12px; color: #8696a0; }
        .chat-msg { font-size: 14px; color: #8696a0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .status-section-title { padding: 12px 16px; font-size: 13px; color: #8696a0; font-weight: bold; text-transform: uppercase; }
        .btn-add-status { background: #202c33; border: none; width: 100%; padding: 14px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer; text-align: left; color: #e9edef; border-bottom: 1px solid #1f2c34; }
        .btn-add-status:active { background: #2a3942; }

        #room-screen { position: fixed; inset: 0; background: #0b141a; display: none; flex-direction: column; z-index: 1000; }
        .room-header { background: #202c33; padding: 10px 16px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: bold; border-bottom: 1px solid #222d34; flex-shrink: 0; color: #e9edef; }
        .room-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: #0b141a; }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: #202c33; color: #e9edef; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .bubble.sent { background: #005c4b; align-self: flex-end; }
        .room-footer { background: #202c33; padding: 8px 12px; display: flex; gap: 10px; align-items: center; flex-shrink: 0; border-top: 1px solid #222d34; }
        .room-footer input[type="text"] { flex: 1; background: #2a3942; border: none; padding: 10px 16px; border-radius: 24px; color: #fff; font-size: 15px; outline: none; }
        .btn-send { background: #00a884; border: none; width: 42px; height: 42px; border-radius: 50%; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 18px; }
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color: #00a884; margin-bottom: 12px;">WhatsApp</h2>
        <p style="color: #8696a0; margin-bottom: 20px; font-size: 14px;">Digite seu nome para entrar:</p>
        <input type="text" id="username" placeholder="Seu nome">
        <button onclick="entrar()">Avançar</button>
    </div>

    <div class="header">
        <span>WhatsApp</span>
        <span onclick="criarGrupo()" style="cursor:pointer; font-size: 18px; color:#00a884;" title="Novo Grupo">👥➕</span>
    </div>

    <div class="nav-tabs">
        <div class="nav-tab active" onclick="mudarAba('chats', this)">Conversas</div>
        <div class="nav-tab" onclick="mudarAba('status', this)">Status</div>
    </div>

    <!-- ABA CONVERSAS -->
    <div id="tab-chats" class="tab-content active">
        <div class="chat-item" onclick="abrirChat('Lu')">
            <div class="avatar" style="background: #e91e63;">L</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">Lu</span><span class="chat-time">06:00</span></div>
                <div class="chat-msg">ta bom</div>
            </div>
        </div>
        <div class="chat-item" onclick="abrirChat('ITABOA NOTÍCIAS 2026')">
            <div class="avatar" style="background: #25d366;">IN</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">ITABOA NOTÍCIAS 2026</span><span class="chat-time">05:35</span></div>
                <div class="chat-msg">Silvinho: !(((</div>
            </div>
        </div>
        <div class="chat-item" onclick="abrirChat('FAMÍLIA GOUDIM')">
            <div class="avatar" style="background: #ff9800;">FG</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">FAMÍLIA GOUDIM</span><span class="chat-time">20:15</span></div>
                <div class="chat-msg">Dirce: Boa noite</div>
            </div>
        </div>
    </div>

    <!-- ABA STATUS -->
    <div id="tab-status" class="tab-content">
        <button class="btn-add-status" onclick="postarStatus()">
            <div class="avatar" style="background: #00a884; font-size: 22px;">➕</div>
            <div class="chat-info">
                <div class="chat-name">Meu status</div>
                <div class="chat-msg">Toque para atualizar o status</div>
            </div>
        </button>
        <div class="status-section-title">Atualizações recentes</div>
        <div id="lista-status">
            <div class="chat-item">
                <div class="avatar" style="background: #3f51b5; border: 2px solid #00a884;">LF</div>
                <div class="chat-info">
                    <div class="chat-top"><span class="chat-name">Lucio Flávio</span><span class="chat-time">Há 45 min</span></div>
                    <div class="chat-msg">Trabalhando duro por aqui 🚀</div>
                </div>
            </div>
        </div>
    </div>

    <!-- TELA DE CHAT INDIVIDUAL/GRUPO -->
    <div id="room-screen">
        <div class="room-header">
            <span onclick="fecharChat()" style="cursor:pointer; font-size: 22px;">⬅️</span>
            <span id="room-title" style="flex:1;">Chat</span>
        </div>
        <div class="room-messages" id="mensagens"></div>
        <div class="room-footer">
            <input type="text" id="mensagem-input" placeholder="Mensagem" onkeypress="if(event.key==='Enter')enviarTexto()">
            <button class="btn-send" onclick="enviarTexto()">➤</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        let meuNome = ''; let salaAtual = '';

        function entrar() {
            let n = document.getElementById('username').value.trim();
            if(!n) { alert('Digite seu nome!'); return; }
            meuNome = n;
            document.getElementById('login').style.display = 'none';
        }

        function mudarAba(aba, el) {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('tab-' + aba).classList.add('active');
        }

        function postarStatus() {
            let st = prompt("O que está acontecendo no seu status?");
            if(st) {
                let lista = document.getElementById('lista-status');
                lista.insertAdjacentHTML('afterbegin', `<div class="chat-item"><div class="avatar" style="background:#00a884; border: 2px solid #00a884;">${meuNome.charAt(0)}</div><div class="chat-info"><div class="chat-top"><span class="chat-name">${meuNome} (Você)</span><span class="chat-time">Agora</span></div><div class="chat-msg">${st}</div></div></div>`);
                alert("Status publicado com sucesso!");
            }
        }

        function abrirChat(nome) {
            if(!meuNome) { alert('Identifique-se primeiro.'); return; }
            salaAtual = nome;
            document.getElementById('room-title').innerText = nome;
            document.getElementById('mensagens').innerHTML = '';
            document.getElementById('room-screen').style.display = 'flex';
            socket.emit('join', { username: meuNome, room: salaAtual });
        }

        function fecharChat() {
            socket.emit('leave', { username: meuNome, room: salaAtual });
            document.getElementById('room-screen').style.display = 'none';
        }

        function criarGrupo() {
            let g = prompt("Nome do novo grupo:");
            if(g) {
                let lista = document.getElementById('tab-chats');
                lista.insertAdjacentHTML('afterbegin', `<div class="chat-item" onclick="abrirChat('${g}')"><div class="avatar" style="background:#00a884;">👥</div><div class="chat-info"><div class="chat-top"><span class="chat-name">${g}</span><span class="chat-time">Agora</span></div><div class="chat-msg">Grupo criado</div></div></div>`);
                abrirChat(g);
            }
        }

        function enviarTexto() {
            let input = document.getElementById('mensagem-input');
            let text = input.value.trim();
            if(!text) return;
            socket.emit('message', { room: salaAtual, username: meuNome, content: text });
            input.value = '';
        }

        socket.on('message', function(data) {
            if(data.room === salaAtual) {
                let box = document.getElementById('mensagens');
                let isMe = data.username === meuNome;
                let cls = isMe ? 'bubble sent' : 'bubble';
                box.innerHTML += `<div class="${cls}"><div><strong>${!isMe ? data.username + ': ' : ''}</strong>${data.content}</div></div>`;
                box.scrollTop = box.scrollHeight;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('leave')
def on_leave(data):
    pass

@socketio.on('message')
def handle_message(data):
    emit('message', data, room=data['room'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
