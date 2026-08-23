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
        .room-header { background: #202c33; padding: 10px 16px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: bold; border-bottom: 1px solid #222d34; flex-shrink: 0; color: #e9edef; }
        .room-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: #0b141a; }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: #202c33; color: #e9edef; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .bubble.sent { background: #005c4b; align-self: flex-end; }
        .bubble img, .bubble video { width: 100%; border-radius: 6px; margin-top: 4px; max-height: 250px; object-fit: cover; }
        .room-footer { background: #202c33; padding: 8px 12px; display: flex; gap: 10px; align-items: center; flex-shrink: 0; border-top: 1px solid #222d34; }
        .room-footer input[type="text"] { flex: 1; background: #2a3942; border: none; padding: 10px 16px; border-radius: 24px; color: #fff; font-size: 15px; outline: none; }
        .btn-send, .btn-icon { background: none; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 4px; }
        .btn-send { background: #00a884; width: 42px; height: 42px; border-radius: 50%; color: white; flex-shrink: 0; }
        svg { width: 24px; height: 24px; fill: currentColor; }
        #attachment-menu { position: fixed; bottom: 65px; left: 16px; right: 16px; background: #202c33; border-radius: 16px; padding: 16px; display: none; grid-template-columns: repeat(3, 1fr); gap: 16px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4); border: 1px solid #222d34; z-index: 1005; }
        .att-option { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #e9edef; }
        .att-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; }
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
        <button class="btn-icon" onclick="criarGrupo()" style="color: #00a884;" title="Novo Grupo">
            <svg viewBox="0 0 24 24"><path d="M15 14c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4zm-9-4V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 2c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z"/></svg>
        </button>
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
            <button class="btn-icon" onclick="fecharChat()" style="color: #aebac1;">
                <svg viewBox="0 0 24 24"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
            </button>
            <span id="room-title" style="flex:1;">Chat</span>
        </div>
        <div class="room-messages" id="mensagens"></div>
        
        <div id="attachment-menu">
            <div class="att-option" onclick="document.getElementById('input-img').click()">
                <div class="att-icon" style="background:#bf59cf;">
                    <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                </div>
                <span>Foto</span>
            </div>
            <div class="att-option" onclick="document.getElementById('input-vid').click()">
                <div class="att-icon" style="background:#d32f2f;">
                    <svg viewBox="0 0 24 24"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>
                </div>
                <span>Vídeo</span>
            </div>
            <div class="att-option" onclick="enviarAudio()">
                <div class="att-icon" style="background:#00a884;">
                    <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20h2v-3.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z"/></svg>
                </div>
                <span>Áudio</span>
            </div>
        </div>
        <input type="file" id="input-img" style="display:none" accept="image/*" onchange="enviarMidia(event, 'image')">
        <input type="file" id="input-vid" style="display:none" accept="video/*" onchange="enviarMidia(event, 'video')">

        <div class="room-footer">
            <button class="btn-icon" onclick="toggleAnexo()" style="color: #8696a0;" title="Anexar">
                <svg viewBox="0 0 24 24"><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
            </button>
            <input type="text" id="mensagem-input" placeholder="Mensagem" onkeypress="if(event.key==='Enter')enviarTexto()">
            <button class="btn-send" onclick="enviarTexto()" title="Enviar">
                <svg viewBox="0 0 24 24" style="width:20px;height:20px;"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
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

        socket.on('message', function(data) {
            let box = document.getElementById('mensagens');
            let isMe = data.username === meuNome;
            let cls = isMe ? 'bubble sent' : 'bubble';
            let html = '';
            if(data.type === 'image') {
                html = `<img src="${data.content}">`;
            } else if(data.type === 'video') {
                html = `<video controls src="${data.content}"></video>`;
            } else {
                html = `<div><strong>${!isMe ? data.username + ': ' : ''}</strong>${data.content}</div>`;
            }
            box.innerHTML += `<div class="${cls}">${html}</div>`;
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
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    
