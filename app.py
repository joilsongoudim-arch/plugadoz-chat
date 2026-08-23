from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Plugadoz Chat</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.min.js"></script>
    <style>
        :root {
            --bg-body: #ffffff;
            --surface: #ffffff;
            --text-main: #111b21;
            --text-sub: #667781;
            --green-wa: #00a884;
            --green-badge: #25d366;
            --green-pill: #d2f5ea;
            --green-pill-text: #0b4a3b;
            --search-bg: #f0f2f5;
            --chip-bg: #f0f2f5;
            --border-color: #e9edef;
            --chat-bg: #efeae2;
            --bubble-sent: #d9fdd3;
            --bubble-recv: #ffffff;
            --menu-bg: #ffffff;
        }
        [data-theme="dark"] {
            --bg-body: #111b21;
            --surface: #202c33;
            --text-main: #e9edef;
            --text-sub: #8696a0;
            --green-wa: #00a884;
            --green-badge: #00a884;
            --green-pill: #005c4b;
            --green-pill-text: #e9edef;
            --search-bg: #111b21;
            --chip-bg: #222d34;
            --border-color: #222d34;
            --chat-bg: #0b141a;
            --bubble-sent: #005c4b;
            --bubble-recv: #202c33;
            --menu-bg: #233138;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg-body); color: var(--text-main); }
        .app-layout { display: flex; flex-direction: column; height: 100vh; height: 100dvh; width: 100vw; position: relative; }
        
        /* Tela de Login Inicial para definir o nome do usuário */
        #login-screen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: var(--bg-body); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 99999; padding: 20px; }
        .login-card { background: var(--surface); padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); width: 100%; max-width: 360px; text-align: center; border: 1px solid var(--border-color); }
        .login-card h2 { margin-bottom: 20px; color: var(--green-wa); }
        .login-card input { width: 100%; padding: 12px 16px; border-radius: 24px; border: 1px solid var(--border-color); background: var(--search-bg); color: var(--text-main); font-size: 16px; outline: none; margin-bottom: 16px; text-align: center; }
        .login-card button { width: 100%; padding: 12px; border-radius: 24px; border: none; background: var(--green-wa); color: white; font-size: 16px; font-weight: bold; cursor: pointer; }

        /* Header */
        .header { background: var(--surface); padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; border-bottom: 1px solid var(--border-color); }
        .brand { font-size: 22px; font-weight: 700; color: var(--green-wa); }
        
        /* Container Principal */
        .container { flex: 1; overflow-y: auto; background: var(--bg-body); display: flex; flex-direction: column; }
        .room-item { display: flex; align-items: center; padding: 14px 16px; gap: 14px; cursor: pointer; border-bottom: 1px solid var(--border-color); }
        .room-item:active { background: var(--border-color); }
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 18px; color: white; background: var(--green-wa); flex-shrink: 0; }
        .room-info { flex: 1; }
        .room-name { font-size: 16px; font-weight: 600; }
        .room-desc { font-size: 14px; color: var(--text-sub); }

        /* Tela de Chat Real */
        #chat-screen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; height: 100dvh; background: var(--chat-bg); display: none; flex-direction: column; z-index: 9999; }
        #chat-screen.active { display: flex; }
        .fs-header { background: var(--surface); padding: 10px 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border-color); }
        .chat-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: var(--bubble-recv); color: var(--text-main); box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .bubble.sent { background: var(--bubble-sent); align-self: flex-end; }
        .bubble img, .bubble video { width: 100%; border-radius: 6px; margin-top: 4px; }
        .msg-meta { font-size: 10px; color: var(--text-sub); text-align: right; margin-top: 2px; }
        
        .chat-footer { background: var(--surface); padding: 8px 12px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--border-color); }
        .msg-box { flex: 1; background: var(--search-bg); border-radius: 24px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; border: 1px solid var(--border-color); }
        .msg-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        .btn-circle { background: var(--green-wa); border: none; width: 42px; height: 42px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
    </style>
</head>
<body>

    <!-- Tela de Identificação -->
    <div id="login-screen">
        <div class="login-card">
            <h2>Plugadoz Chat</h2>
            <p style="color: var(--text-sub); margin-bottom: 16px; font-size: 14px;">Digite seu nome para entrar e falar com seus amigos:</p>
            <input type="text" id="username-input" placeholder="Seu nome ou apelido">
            <button onclick="entrarApp()">Entrar no Chat</button>
        </div>
    </div>

    <div class="app-layout">
        <div class="header">
            <span class="brand">Plugadoz Chat</span>
            <span class="material-icons-outlined" style="cursor:pointer;" onclick="toggleTheme()">brightness_medium</span>
        </div>

        <div class="container">
            <div style="padding: 16px 16px 8px 16px; font-size: 13px; font-weight: bold; color: var(--text-sub);">SALAS DISPONÍVEIS PARA CONVERSAR</div>
            
            <div class="room-item" onclick="joinRoom('Geral')">
                <div class="avatar">G</div>
                <div class="room-info">
                    <div class="room-name">Sala Geral</div>
                    <div class="room-desc">Toque para entrar e conversar com todos</div>
                </div>
            </div>
            
            <div class="room-item" onclick="joinRoom('Amigos')">
                <div class="avatar" style="background:#25d366;">A</div>
                <div class="room-info">
                    <div class="room-name">Turma de Amigos</div>
                    <div class="room-desc">Conversas livres da galera</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Tela de Mensagens da Sala -->
    <div id="chat-screen">
        <div class="fs-header">
            <span class="material-icons-outlined" onclick="leaveRoom()" style="cursor:pointer;">arrow_back</span>
            <div class="avatar" style="width:36px; height:36px; font-size:14px;" id="room-avatar-mini">G</div>
            <div style="flex:1;">
                <div style="font-weight:600; font-size:16px;" id="room-title">Sala</div>
                <div style="font-size:11px; color:var(--text-sub);" id="room-status">Conectado em tempo real</div>
            </div>
        </div>
        
        <div class="chat-body" id="chat-messages"></div>
        
        <div class="chat-footer">
            <input type="file" id="media-input" style="display:none" accept="image/*" onchange="sendMedia(event)">
            <span class="material-icons-outlined" style="cursor:pointer; color:var(--text-sub);" onclick="document.getElementById('media-input').click()">image</span>
            <div class="msg-box">
                <input type="text" id="message-input" placeholder="Digite sua mensagem..." onkeypress="if(event.key === 'Enter') sendMessage()">
            </div>
            <button class="btn-circle" onclick="sendMessage()"><span class="material-icons-outlined">send</span></button>
        </div>
    </div>

    <script>
        const socket = io();
        let currentUser = '';
        let currentRoom = '';

        function entrarApp() {
            let name = document.getElementById('username-input').value.trim();
            if(!name) {
                alert('Por favor, digite seu nome!');
                return;
            }
            currentUser = name;
            document.getElementById('login-screen').style.display = 'none';
        }

        function joinRoom(room) {
            if(!currentUser) {
                alert('Identifique-se primeiro.');
                return;
            }
            currentRoom = room;
            document.getElementById('room-title').innerText = room;
            document.getElementById('room-avatar-mini').innerText = room.substring(0,1);
            document.getElementById('chat-messages').innerHTML = '';
            document.getElementById('chat-screen').classList.add('active');
            
            socket.emit('join', { username: currentUser, room: room });
        }

        function leaveRoom() {
            socket.emit('leave', { username: currentUser, room: currentRoom });
            document.getElementById('chat-screen').classList.remove('active');
        }

        function sendMessage() {
            let input = document.getElementById('message-input');
            let text = input.value.trim();
            if(!text) return;

            socket.emit('message', {
                room: currentRoom,
                username: currentUser,
                type: 'text',
                content: text
            });
            input.value = '';
        }

        function sendMedia(event) {
            let file = event.target.files[0];
            if(!file) return;
            let reader = new FileReader();
            reader.onload = function(e) {
                socket.emit('message', {
                    room: currentRoom,
                    username: currentUser,
                    type: 'image',
                    content: e.target.result
                });
            };
            reader.readAsDataURL(file);
        }

        socket.on('message', function(data) {
            let body = document.getElementById('chat-messages');
            let isMe = data.username === currentUser;
            let bubbleClass = isMe ? 'bubble sent' : 'bubble recv';
            
            let contentHtml = '';
            if(data.type === 'image') {
                contentHtml = `<img src="${data.content}">`;
            } else {
                contentHtml = `<div><strong>${!isMe ? data.username + ': ' : ''}</strong>${data.content}</div>`;
            }

            body.innerHTML += `<div class="${bubbleClass}">${contentHtml}<div class="msg-meta">${data.username}</div></div>`;
            body.scrollTop = body.scrollHeight;
        });

        function toggleTheme() {
            let html = document.documentElement;
            let current = html.getAttribute('data-theme');
            html.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'username': 'Sistema', 'type': 'text', 'content': f"{data['username']} entrou na sala."}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    emit('message', {'username': 'Sistema', 'type': 'text', 'content': f"{data['username']} saiu da sala."}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    emit('message', data, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
