import os
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-whatsapp-master-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(20), default='text')
    timestamp = db.Column(db.String(10), default=lambda: datetime.now().strftime('%H:%M'))

with app.app_context():
    db.create_all()

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
        #login { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #111b21; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; padding: 20px; text-align: center; }
        #login input { width: 100%; max-width: 320px; padding: 14px 20px; border-radius: 24px; border: 1px solid #222d34; background: #202c33; color: #fff; font-size: 16px; margin-bottom: 16px; text-align: center; outline: none; }
        #login button { width: 100%; max-width: 320px; padding: 14px; border-radius: 24px; border: none; background: #00a884; color: white; font-size: 16px; font-weight: bold; cursor: pointer; }
        .header { background: #202c33; padding: 14px 16px; font-size: 20px; font-weight: bold; color: #00a884; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222d34; flex-shrink: 0; }
        .chat-list { flex: 1; overflow-y: auto; background: #111b21; }
        .chat-item { display: flex; align-items: center; padding: 12px 16px; gap: 14px; cursor: pointer; border-bottom: 1px solid #1f2c34; }
        .chat-item:active { background: #202c33; }
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; flex-shrink: 0; font-size: 16px; }
        .chat-info { flex: 1; min-width: 0; }
        .chat-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .chat-name { font-size: 16px; font-weight: 600; color: #e9edef; }
        .chat-time { font-size: 12px; color: #8696a0; }
        .chat-msg { font-size: 14px; color: #8696a0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        #room-screen { position: fixed; top: 0; left: 0; width: 100%; height: 100%; height: 100dvh; background: #0b141a; display: none; flex-direction: column; z-index: 1000; }
        .room-header { background: #202c33; padding: 10px 16px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: bold; border-bottom: 1px solid #222d34; flex-shrink: 0; }
        .room-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: #0b141a; }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: #202c33; color: #e9edef; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .bubble.sent { background: #005c4b; align-self: flex-end; }
        .bubble img, .bubble video { width: 100%; border-radius: 6px; margin-top: 4px; max-height: 250px; object-fit: cover; }
        .room-footer { background: #202c33; padding: 8px 12px; display: flex; gap: 10px; align-items: center; flex-shrink: 0; border-top: 1px solid #222d34; }
        .room-footer input[type="text"] { flex: 1; background: #2a3942; border: none; padding: 10px 16px; border-radius: 24px; color: #fff; font-size: 15px; outline: none; }
        .btn-send { background: #00a884; border: none; width: 42px; height: 42px; border-radius: 50%; color: white; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        #attachment-menu { position: fixed; bottom: 65px; left: 16px; right: 16px; background: #202c33; border-radius: 16px; padding: 16px; display: none; grid-template-columns: repeat(3, 1fr); gap: 16px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4); border: 1px solid #222d34; z-index: 1005; }
        .att-option { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #e9edef; }
        .att-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; color: white; }
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
        <span onclick="criarGrupo()" style="cursor:pointer; font-size: 20px;" title="Novo Grupo">👥➕</span>
    </div>

    <div class="chat-list" id="lista-conversas">
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
        <div class="chat-item" onclick="abrirChat('Dime')">
            <div class="avatar" style="background: #607d8b;">D</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">Dime</span><span class="chat-time">Ontem</span></div>
                <div class="chat-msg">Veio ontem de moto...</div>
            </div>
        </div>
        <div class="chat-item" onclick="abrirChat('Lucio Flávio')">
            <div class="avatar" style="background: #3f51b5;">LF</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">Lucio Flávio</span><span class="chat-time">Ontem</span></div>
                <div class="chat-msg">Kkk criativo né.</div>
            </div>
        </div>
        <div class="chat-item" onclick="abrirChat('Reinaldo Goudim')">
            <div class="avatar" style="background: #d32f2f;">RG</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">Reinaldo Goudim</span><span class="chat-time">Ontem</span></div>
                <div class="chat-msg">Mensagem de voz</div>
            </div>
        </div>
        <div class="chat-item" onclick="abrirChat('micaella')">
            <div class="avatar" style="background: #e040fb;">M</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">micaella</span><span class="chat-time">Ontem</span></div>
                <div class="chat-msg">Já já acaba</div>
            </div>
        </div>
        <div class="chat-item" onclick="abrirChat('FAMÍLIA GOUDIM')">
            <div class="avatar" style="background: #ff9800;">FG</div>
            <div class="chat-info">
                <div class="chat-top"><span class="chat-name">FAMÍLIA GOUDIM 👨‍👩‍👦</span><span class="chat-time">20:15</span></div>
                <div class="chat-msg">Dirce: Boa noite</div>
            </div>
        </div>
    </div>

    <div id="room-screen">
        <div class="room-header">
            <span onclick="fecharChat()" style="cursor:pointer; font-size: 22px;">⬅️</span>
            <span id="room-title" style="flex:1;">Chat</span>
        </div>
        <div class="room-messages" id="mensagens"></div>
        
        <div id="attachment-menu">
            <div class="att-option" onclick="document.getElementById('input-img').click()"><div class="att-icon" style="background:#bf59cf;">🖼️</div><span>Foto</span></div>
            <div class="att-option" onclick="document.getElementById('input-vid').click()"><div class="att-icon" style="background:#d32f2f;">📹</div><span>Vídeo</span></div>
            <div class="att-option" onclick="enviarAudio()"><div class="att-icon" style="background:#00a884;">🎤</div><span>Áudio</span></div>
        </div>
        <input type="file" id="input-img" style="display:none" accept="image/*" onchange="enviarMidia(event, 'image')">
        <input type="file" id="input-vid" style="display:none" accept="video/*" onchange="enviarMidia(event, 'video')">

        <div class="room-footer">
            <span onclick="toggleAnexo()" style="cursor:pointer; font-size: 22px;">📎</span>
            <input type="text" id="mensagem-input" placeholder="Mensagem" onkeypress="if(event.key==='Enter')enviarTexto()">
            <button class="btn-send" onclick="enviarTexto()">📤</button>
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
            
            // Buscar histórico do banco
            fetch('/history/' + encodeURIComponent(salaAtual))
                .then(res => res.json())
                .then(data => {
                    let box = document.getElementById('mensagens');
                    data.forEach(msg => adicionarMensagemNaTela(msg));
                    box.scrollTop = box.scrollHeight;
                });
        }

        function fecharChat() {
            socket.emit('leave', { username: meuNome, room: salaAtual });
            document.getElementById('room-screen').style.display = 'none';
            document.getElementById('attachment-menu').style.display = 'none';
        }

        function toggleAnexo() {
            let menu = document.getElementById('attachment-menu');
            menu.style.display = menu.style.display === 'grid' ? 'none' : 'grid';
        }

        function criarGrupo() {
            let g = prompt("Nome do novo grupo:");
            if(g) {
                let lista = document.getElementById('lista-conversas');
                lista.insertAdjacentHTML('afterbegin', `<div class="chat-item" onclick="abrirChat('${g}')"><div class="avatar" style="background:#00a884;">👥</div><div class="chat-info"><div class="chat-top"><span class="chat-name">${g}</span><span class="chat-time">Agora</span></div><div class="chat-msg">Grupo criado</div></div></div>`);
                abrirChat(g);
            }
        }

        function enviarTexto() {
            let input = document.getElementById('mensagem-input');
            let text = input.value.trim();
            if(!text) return;
            socket.emit('message', { room: salaAtual, username: meuNome, content: text, type: 'text' });
            input.value = '';
        }

        function enviarMidia(event, type) {
            let file = event.target.files[0];
            if(!file) return;
            let reader = new FileReader();
            reader.onload = function(e) {
                socket.emit('message', { room: salaAtual, username: meuNome, content: e.target.result, type: type });
            };
            reader.readAsDataURL(file);
            document.getElementById('attachment-menu').style.display = 'none';
        }

        function enviarAudio() {
            socket.emit('message', { room: salaAtual, username: meuNome, content: '🎤 Mensagem de voz (0:03)', type: 'audio' });
            document.getElementById('attachment-menu').style.display = 'none';
        }

        function adicionarMensagemNaTela(data) {
            let box = document.getElementById('mensagens');
            let isMe = data.username === meuNome;
            let cls = isMe ? 'bubble sent' : 'bubble';
            let html = '';
            if(data.msg_type === 'image') {
                html = `<img src="${data.content}">`;
            } else if(data.msg_type === 'video') {
                html = `<video controls src="${data.content}"></video>`;
            } else {
                html = `<div><strong>${!isMe ? data.username + ': ' : ''}</strong>${data.content}</div>`;
            }
            box.innerHTML += `<div class="${cls}">${html}</div>`;
            box.scrollTop = box.scrollHeight;
        }

        socket.on('message', function(data) {
            adicionarMensagemNaTela(data);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/history/<room>')
def get_history(room):
    messages = Message.query.filter_by(room=room).all()
    result = []
    for m in messages:
        result.append({
            'username': m.username,
            'content': m.content,
            'msg_type': m.msg_type,
            'timestamp': m.timestamp
        })
    return jsonify(result)

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('leave')
def on_leave(data):
    pass

@socketio.on('message')
def handle_message(data):
    # Salvar no banco de dados local SQLite
    new_msg = Message(
        room=data['room'],
        username=data['username'],
        content=data['content'],
        msg_type=data.get('type', 'text')
    )
    db.session.add(new_msg)
    db.session.commit()

    emit('message', {
        'username': data['username'],
        'content': data['content'],
        'msg_type': data.get('type', 'text'),
        'timestamp': new_msg.timestamp
    }, room=data['room'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
