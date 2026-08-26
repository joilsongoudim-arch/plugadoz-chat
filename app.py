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
    <title>Plugadoz</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #111b21; color: #e9edef; height: 100vh; height: 100dvh; display: flex; flex-direction: column; overflow: hidden; }
        
        #login { position: fixed; inset: 0; background: #111b21; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; padding: 20px; text-align: center; }
        #login input { width: 100%; max-width: 320px; padding: 14px 20px; border-radius: 24px; border: 1px solid #222d34; background: #202c33; color: #fff; font-size: 16px; margin-bottom: 16px; text-align: center; outline: none; }
        #login button { width: 100%; max-width: 320px; padding: 14px; border-radius: 24px; border: none; background: #00a884; color: white; font-size: 16px; font-weight: bold; cursor: pointer; }
        
        .header { background: #111b21; padding: 14px 16px; font-size: 22px; font-weight: bold; color: #00a884; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .header-icons { display: flex; gap: 20px; font-size: 20px; color: #aebac1; cursor: pointer; align-items: center; position: relative; }

        /* Menu Dropdown */
        #menu-dropdown { position: absolute; right: 10px; top: 45px; background: #233138; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: none; flex-direction: column; z-index: 2000; width: 160px; }
        .menu-item { padding: 12px 16px; color: #e9edef; font-size: 14px; cursor: pointer; }
        .menu-item:hover { background: #182229; }

        /* Filtros superiores */
        .filters { display: flex; gap: 8px; padding: 8px 16px; background: #111b21; overflow-x: auto; flex-shrink: 0; }
        .filter-chip { background: #202c33; color: #8696a0; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; white-space: nowrap; cursor: pointer; }
        .filter-chip.active { background: #005c4b; color: #e9edef; }

        .content-area { flex: 1; overflow-y: auto; background: #111b21; }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }

        .chat-item { display: flex; align-items: center; padding: 10px 16px; gap: 14px; cursor: pointer; }
        .chat-item:active { background: #202c33; }
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; flex-shrink: 0; font-size: 16px; }
        .chat-info { flex: 1; min-width: 0; border-bottom: 1px solid #1f2c34; padding-bottom: 10px; }
        .chat-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .chat-name { font-size: 16px; font-weight: 600; color: #e9edef; }
        .chat-time { font-size: 12px; color: #8696a0; }
        .chat-msg { font-size: 14px; color: #8696a0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* Barra de navegação inferior */
        .bottom-nav { display: flex; background: #111b21; border-top: 1px solid #222d34; height: 60px; flex-shrink: 0; justify-content: space-around; align-items: center; }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: #8696a0; font-size: 11px; cursor: pointer; gap: 4px; flex: 1; }
        .nav-item span:first-child { font-size: 20px; }
        .nav-item.active { color: #00a884; }

        /* Tela de Chat Individual */
        #room-screen { position: fixed; inset: 0; background: #0b141a; display: none; flex-direction: column; z-index: 1000; }
        .room-header { background: #202c33; padding: 10px 16px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: bold; border-bottom: 1px solid #222d34; flex-shrink: 0; color: #e9edef; }
        .room-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: #0b141a; }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: #202c33; color: #e9edef; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .bubble.sent { background: #005c4b; align-self: flex-end; }
        .bubble img { max-width: 100%; border-radius: 6px; margin-top: 4px; }
        .room-footer { background: #202c33; padding: 8px 12px; display: flex; gap: 8px; align-items: center; flex-shrink: 0; border-top: 1px solid #222d34; }
        .room-footer input[type="text"] { flex: 1; background: #2a3942; border: none; padding: 10px 16px; border-radius: 24px; color: #fff; font-size: 15px; outline: none; }
        .btn-action { background: transparent; border: none; color: #8696a0; font-size: 20px; cursor: pointer; padding: 4px; }
        .btn-send { background: #00a884; border: none; width: 40px; height: 40px; border-radius: 50%; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 16px; }
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color: #00a884; margin-bottom: 12px;">Plugadoz</h2>
        <p style="color: #8696a0; margin-bottom: 20px; font-size: 14px;">Digite seu nome para entrar:</p>
        <input type="text" id="username" placeholder="Seu nome">
        <button onclick="entrar()">Avançar</button>
    </div>

    <div class="header">
        <span>Plugadoz</span>
        <div class="header-icons">
            <span onclick="abrirCameraGeral()" title="Câmera">📷</span>
            <span onclick="toggleMenu()" title="Menu">⋮</span>
            <div id="menu-dropdown">
                <div class="menu-item" onclick="editarPerfil()">Editar Perfil</div>
                <div class="menu-item" onclick="criarGrupo()">Novo grupo</div>
                <div class="menu-item" onclick="alert('Plugadoz v2.6 - Conectado')">Sobre</div>
            </div>
        </div>
    </div>

    <!-- Filtros de conversas -->
    <div class="filters" id="chat-filters">
        <div class="filter-chip active">Todas</div>
        <div class="filter-chip">Não lidas</div>
        <div class="filter-chip">Favoritos</div>
        <div class="filter-chip" onclick="criarGrupo()">Grupos ➕</div>
    </div>

    <div class="content-area">
        <!-- ABA CONVERSAS -->
        <div id="pane-conversas" class="tab-pane active">
            <div class="chat-item" onclick="abrirChat('Pedro Ferreira')">
                <div class="avatar" style="background: #e91e63;">P</div>
                <div class="chat-info">
                    <div class="chat-top"><span class="chat-name">Pedro Ferreira</span><span class="chat-time">16:54</span></div>
                    <div class="chat-msg">Ta</div>
                </div>
            </div>
            <div class="chat-item" onclick="abrirChat('ITABOA NOTÍCIAS 2026')">
                <div class="avatar" style="background: #25d366;">IN</div>
                <div class="chat-info">
                    <div class="chat-top"><span class="chat-name">ITABOA NOTÍCIAS 2026</span><span class="chat-time">14:10</span></div>
                    <div class="chat-msg">Cunhado 99 @: https://vt.tiktok.com...</div>
                </div>
            </div>
            <div class="chat-item" onclick="abrirChat('Lucy')">
                <div class="avatar" style="background: #ff9800;">L</div>
                <div class="chat-info">
                    <div class="chat-top"><span class="chat-name">Lucy</span><span class="chat-time">Ontem</span></div>
                    <div class="chat-msg">Xe não tem hora</div>
                </div>
            </div>
        </div>

        <!-- ABA ATUALIZAÇÕES (STATUS) -->
        <div id="pane-atualizacoes" class="tab-pane">
            <div style="padding: 16px; font-weight: bold; color: #8696a0; font-size: 13px; text-transform: uppercase;">Status</div>
            <div class="chat-item" onclick="postarStatus()">
                <div class="avatar" style="background: #00a884; font-size: 22px;">➕</div>
                <div class="chat-info">
                    <div class="chat-top"><span class="chat-name">Meu status</span></div>
                    <div class="chat-msg">Toque para atualizar o status</div>
                </div>
            </div>
            <div style="padding: 16px; font-weight: bold; color: #8696a0; font-size: 13px; text-transform: uppercase;">Atualizações recentes</div>
            <div id="lista-status-posts"></div>
        </div>

        <!-- ABA COMUNIDADES -->
        <div id="pane-comunidades" class="tab-pane">
            <div style="padding: 24px; text-align: center; color: #8696a0;">
                <h3>Comunidades</h3>
                <p style="font-size: 14px; margin-top: 8px;">Organize seus grupos facilmente em comunidades.</p>
            </div>
        </div>

        <!-- ABA LIGAÇÕES -->
        <div id="pane-ligacoes" class="tab-pane">
            <div style="padding: 24px; text-align: center; color: #8696a0;">
                <h3>Chamadas</h3>
                <p style="font-size: 14px; margin-top: 8px;">Toque para iniciar uma chamada de voz ou vídeo.</p>
            </div>
        </div>
    </div>

    <!-- BARRA DE NAVEGAÇÃO INFERIOR -->
    <div class="bottom-nav">
        <div class="nav-item active" onclick="mudarAba('conversas', this)">
            <span>💬</span>
            <span>Conversas</span>
        </div>
        <div class="nav-item" onclick="mudarAba('atualizacoes', this)">
            <span>⭕</span>
            <span>Atualizações</span>
        </div>
        <div class="nav-item" onclick="mudarAba('comunidades', this)">
            <span>👥</span>
            <span>Comunidades</span>
        </div>
        <div class="nav-item" onclick="mudarAba('ligacoes', this)">
            <span>📞</span>
            <span>Ligações</span>
        </div>
    </div>

    <!-- TELA DO CHAT -->
    <div id="room-screen">
        <div class="room-header">
            <span onclick="fecharChat()" style="cursor:pointer; font-size: 22px;">⬅️</span>
            <span id="room-title" style="flex:1;">Chat</span>
        </div>
        <div class="room-messages" id="mensagens"></div>
        <div class="room-footer">
            <input type="file" id="file-input" style="display:none" accept="image/*" onchange="enviarFoto(this)">
            <button class="btn-action" onclick="document.getElementById('file-input').click()" title="Enviar Foto">📎</button>
            <input type="text" id="mensagem-input" placeholder="Mensagem" onkeypress="if(event.key==='Enter')enviarTexto()">
            <button class="btn-action" id="btn-audio" onclick="gravarAudio()" title="Gravar Áudio">🎤</button>
            <button class="btn-send" onclick="enviarTexto()">➤</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        let meuNome = ''; let salaAtual = '';
        let mediaRecorder; let audioChunks = [];

        function entrar() {
            let n = document.getElementById('username').value.trim();
            if(!n) { alert('Digite seu nome!'); return; }
            meuNome = n;
            document.getElementById('login').style.display = 'none';
        }

        function toggleMenu() {
            let m = document.getElementById('menu-dropdown');
            m.style.display = m.style.display === 'flex' ? 'none' : 'flex';
        }

        function editarPerfil() {
            toggleMenu();
            let novo = prompt("Editar seu nome de perfil:", meuNome);
            if(novo) { meuNome = novo; alert("Perfil atualizado com sucesso!"); }
        }

        function mudarAba(aba, el) {
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('pane-' + aba).classList.add('active');
            document.getElementById('chat-filters').style.display = (aba === 'conversas') ? 'flex' : 'none';
        }

        function postarStatus() {
            let st = prompt("Digite seu novo status:");
            if(st) {
                let lista = document.getElementById('lista-status-posts');
                lista.insertAdjacentHTML('afterbegin', `<div class="chat-item"><div class="avatar" style="background:#00a884; border: 2px solid #00a884;">${meuNome.charAt(0)}</div><div class="chat-info"><div class="chat-top"><span class="chat-name">${meuNome}</span><span class="chat-time">Agora</span></div><div class="chat-msg">${st}</div></div></div>`);
                alert("Status publicado!");
            }
        }

        function abrirCameraGeral() {
            let input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.capture = 'environment';
            input.onchange = e => {
                alert("Foto capturada com sucesso!");
            };
            input.click();
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
            if(document.getElementById('menu-dropdown').style.display === 'flex') toggleMenu();
            let g = prompt("Nome do novo grupo:");
            if(g) {
                let lista = document.getElementById('pane-conversas');
                lista.insertAdjacentHTML('afterbegin', `<div class="chat-item" onclick="abrirChat('${g}')"><div class="avatar" style="background:#00a884;">👥</div><div class="chat-info"><div class="chat-top"><span class="chat-name">${g}</span><span class="chat-time">Agora</span></div><div class="chat-msg">Grupo criado</div></div></div>`);
                abrirChat(g);
            }
        }

        function enviarTexto() {
            let input = document.getElementById('mensagem-input');
            let text = input.value.trim();
            if(!text) return;
            socket.emit('message', { room: salaAtual, username: meuNome, type: 'text', content: text });
            input.value = '';
        }

        function enviarFoto(input) {
            if (input.files && input.files[0]) {
                let reader = new FileReader();
                reader.onload = function (e) {
                    socket.emit('message', { room: salaAtual, username: meuNome, type: 'image', content: e.target.result });
                };
                reader.readAsDataURL(input.files[0]);
            }
        }

        function gravarAudio() {
            let btn = document.getElementById('btn-audio');
            if (!mediaRecorder || mediaRecorder.state === "inactive") {
                navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                    mediaRecorder.onstop = () => {
                        let audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                        let reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = function () {
                            socket.emit('message', { room: salaAtual, username: meuNome, type: 'audio', content: reader.result });
                        };
                    };
                    mediaRecorder.start();
                    btn.style.color = '#00a884';
                    alert("Gravando áudio... Clique no microfone novamente para enviar.");
                }).catch(e => alert("Permissão de microfone negada ou indisponível."));
            } else {
                mediaRecorder.stop();
                btn.style.color = '#8696a0';
            }
        }

        socket.on('message', function(data) {
            if(data.room === salaAtual) {
                let box = document.getElementById('mensagens');
                let isMe = data.username === meuNome;
                let cls = isMe ? 'bubble sent' : 'bubble';
                let htmlContent = '';
                
                if (data.type === 'image') {
                    htmlContent = `<img src="${data.content}">`;
                } else if (data.type === 'audio') {
                    htmlContent = `<audio controls src="${data.content}" style="width:200px; height:35px;"></audio>`;
                } else {
                    htmlContent = `<div>${data.content}</div>`;
                }

                box.innerHTML += `<div class="${cls}"><div><strong>${!isMe ? data.username + ': ' : ''}</strong>${htmlContent}</div></div>`;
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
    
