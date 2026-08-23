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
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background: #111b21; color: #e9edef; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        #login { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #111b21; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 999; padding: 20px; text-align: center; }
        #login input { width: 100%; max-width: 300px; padding: 12px; border-radius: 24px; border: 1px solid #222d34; background: #202c33; color: #fff; font-size: 16px; margin-bottom: 15px; text-align: center; outline: none; }
        #login button { padding: 12px 30px; border-radius: 24px; border: none; background: #00a884; color: white; font-size: 16px; font-weight: bold; cursor: pointer; }
        .header { background: #202c33; padding: 15px; font-size: 20px; font-weight: bold; color: #00a884; display: flex; justify-content: space-between; align-items: center; }
        .chat-list { flex: 1; overflow-y: auto; background: #111b21; }
        .chat-item { display: flex; align-items: center; padding: 12px 16px; gap: 14px; border-bottom: 1px solid #222d34; cursor: pointer; }
        .chat-item:active { background: #202c33; }
        .avatar { width: 48px; height: 48px; border-radius: 50%; background: #00a884; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; flex-shrink: 0; }
        .chat-info { flex: 1; min-width: 0; }
        .chat-name { font-size: 16px; font-weight: 600; color: #e9edef; margin-bottom: 4px; }
        .chat-msg { font-size: 14px; color: #8696a0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        #room-screen { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #0b141a; display: none; flex-direction: column; z-index: 99; }
        .room-header { background: #202c33; padding: 12px 16px; display: flex; align-items: center; gap: 12px; font-size: 18px; font-weight: bold; }
        .room-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        .bubble { max-width: 75%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: #202c33; color: #e9edef; }
        .bubble.sent { background: #005c4b; align-self: flex-end; }
        .room-footer { background: #202c33; padding: 10px; display: flex; gap: 8px; align-items: center; }
        .room-footer input { flex: 1; background: #2a3942; border: none; padding: 10px 16px; border-radius: 24px; color: #fff; font-size: 15px; outline: none; }
        .room-footer button { background: #00a884; border: none; width: 40px; height: 40px; border-radius: 50%; color: white; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color: #00a884; margin-bottom: 20px;">WhatsApp Plugadoz</h2>
        <input type="text" id="username" placeholder="Digite seu nome">
        <button onclick="entrar()">Entrar</button>
    </div>

    <div class="header">
        <span>WhatsApp</span>
        <span onclick="novoGrupo()" style="cursor:pointer; font-size: 18px;">➕ Grupo</span>
    </div>

    <div class="chat-list" id="lista-conversas">
        <div class="chat-item" onclick="abrirChat('Lu')">
            <div class="avatar" style="background: #e91e63;">L</div>
            <div class="chat-info"><div class="chat-name">Lu</div><div class="chat-msg">ta bom</div></div>
        </div>
        <div class="chat-item" onclick="abrirChat('ITABOA NOTÍCIAS 2026')">
            <div class="avatar" style="background: #25d366;">IN</div>
            <div class="chat-info"><div class="chat-name">ITABOA NOTÍCIAS 2026</div><div class="chat-msg">Silvinho: !(((</div></div>
        </div>
        <div class="chat-item" onclick="abrirChat('Dime')">
            <div class="avatar" style="background: #607d8b;">D</div>
            <div class="chat-info"><div class="chat-name">Dime</div><div class="chat-msg">Veio ontem de moto...</div></div>
        </div>
        <div class="chat-item" onclick="abrirChat('Lucio Flávio')">
            <div class="avatar" style="background: #3f51b5;">LF</div>
            <div class="chat-info"><div class="chat-name">Lucio Flávio</div><div class="chat-msg">Kkk criativo né.</div></div>
        </div>
        <div class="chat-item" onclick="abrirChat('Reinaldo Goudim')">
            <div class="avatar" style="background: #d32f2f;">RG</div>
            <div class="chat-info"><div class="chat-name">Reinaldo Goudim</div><div class="chat-msg">Mensagem de voz</div></div>
        </div>
        <div class="chat-item" onclick="abrirChat('micaella')">
            <div class="avatar" style="background: #e040fb;">M</div>
            <div class="chat-info"><div class="chat-name">micaella</div><div class="chat-msg">Já já acaba</div></div>
        </div>
        <div class="chat-item" onclick="abrirChat('FAMÍLIA GOUDIM')">
            <div class="avatar" style="background: #ff9800;">FG</div>
            <div class="chat-info"><div class="chat-name">FAMÍLIA GOUDIM 👨‍👩‍👦</div><div class="chat-msg">Dirce: Boa noite</div></div>
        </div>
    </div>

    <div id="room-screen">
        <div class="room-header">
            <span onclick="fecharChat()" style="cursor:pointer;">⬅️</span>
            <span id="room-title">Chat</span>
        </div>
        <div class="room-messages" id="mensagens"></div>
        <div class="room-footer">
            <input type="text" id="mensagem-input" placeholder="Mensagem" onkeypress="if(event.key==='Enter')enviar()">
            <button onclick="enviar()">➡️</button>
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

        function novoGrupo() {
            let g = prompt("Nome do novo grupo:");
            if(g) {
                let lista = document.getElementById('lista-conversas');
                lista.innerHTML += `<div class="chat-item" onclick="abrirChat('${g}')"><div class="avatar" style="background:#00a884;">👥</div><div class="chat-info"><div class="chat-name">${g}</div><div class="chat-msg">Grupo criado</div></div></div>`;
                abrirChat(g);
            }
        }

        function enviar() {
            let input = document.getElementById('mensagem-input');
            let text = input.value.trim();
            if(!text) return;
            socket.emit('message', { room: salaAtual, username: meuNome, content: text });
            input.value = '';
        }

        socket.on('message', function(data) {
            let box = document.getElementById('mensagens');
            let isMe = data.username === meuNome;
            let cls = isMe ? 'bubble sent' : 'bubble';
            box.innerHTML += `<div class="${cls}"><strong>${!isMe ? data.username + ': ' : ''}</strong>${data.content}</div>`;
            box.scrollTop = box.scrollHeight;
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
    socketio.run(app, host='0.0.0.0', port=10000)
