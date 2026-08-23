from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-whatsapp-key'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WhatsApp</title>
    <style>
        :root {
            --bg-body: #ffffff; --surface: #ffffff; --text-main: #111b21; --text-sub: #667781;
            --green-wa: #00a884; --green-badge: #25d366; --green-pill: #d2f5ea; --green-pill-text: #0b4a3b;
            --search-bg: #f0f2f5; --chip-bg: #f0f2f5; --border-color: #e9edef; --chat-bg: #efeae2;
            --bubble-sent: #d9fdd3; --bubble-recv: #ffffff;
        }
        [data-theme="dark"] {
            --bg-body: #111b21; --surface: #202c33; --text-main: #e9edef; --text-sub: #8696a0;
            --green-wa: #00a884; --green-badge: #00a884; --green-pill: #005c4b; --green-pill-text: #e9edef;
            --search-bg: #111b21; --chip-bg: #222d34; --border-color: #222d34; --chat-bg: #0b141a;
            --bubble-sent: #005c4b; --bubble-recv: #202c33;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg-body); color: var(--text-main); }
        .app-layout { display: flex; flex-direction: column; height: 100vh; height: 100dvh; width: 100vw; position: relative; }
        #login-modal { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: var(--bg-body); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 99999; padding: 20px; }
        .login-card { background: var(--surface); padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); width: 100%; max-width: 360px; text-align: center; border: 1px solid var(--border-color); }
        .login-card h2 { margin-bottom: 16px; color: var(--green-wa); }
        .login-card input { width: 100%; padding: 12px 16px; border-radius: 24px; border: 1px solid var(--border-color); background: var(--search-bg); color: var(--text-main); font-size: 16px; outline: none; margin-bottom: 16px; text-align: center; }
        .login-card button { width: 100%; padding: 12px; border-radius: 24px; border: none; background: var(--green-wa); color: white; font-size: 16px; font-weight: bold; cursor: pointer; }
        .header { background: var(--surface); padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; border-bottom: 1px solid var(--border-color); }
        .brand { font-size: 22px; font-weight: 700; color: var(--green-wa); }
        .header-icons { display: flex; gap: 16px; font-size: 20px; cursor: pointer; }
        .container { flex: 1; overflow-y: auto; position: relative; background: var(--bg-body); padding-bottom: 80px; }
        .tab-content { display: none; height: 100%; }
        .tab-content.active { display: flex; flex-direction: column; }
        .search-container { padding: 8px 16px; }
        .search-box { background: var(--search-bg); border-radius: 24px; padding: 10px 16px; display: flex; align-items: center; gap: 12px; border: 1px solid var(--border-color); }
        .search-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        .filter-bar { display: flex; gap: 8px; padding: 4px 16px 12px 16px; overflow-x: auto; flex-shrink: 0; }
        .filter-bar::-webkit-scrollbar { display: none; }
        .chip { background: var(--chip-bg); color: var(--text-sub); padding: 6px 14px; border-radius: 18px; font-size: 13px; font-weight: 500; white-space: nowrap; cursor: pointer; }
        .chip.active { background: var(--green-pill); color: var(--green-pill-text); font-weight: 600; }
        .chat-list { display: flex; flex-direction: column; }
        .chat-item { display: flex; align-items: center; padding: 10px 16px; gap: 14px; cursor: pointer; }
        .chat-item:active { background: var(--border-color); }
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; color: white; flex-shrink: 0; }
        .chat-info { flex: 1; min-width: 0; }
        .chat-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px; }
        .chat-name { font-size: 16px; font-weight: 600; color: var(--text-main); }
        .chat-time { font-size: 12px; color: var(--text-sub); }
        .chat-bottom { display: flex; justify-content: space-between; align-items: center; }
        .chat-msg { font-size: 14px; color: var(--text-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
        .badge { background: var(--green-badge); color: white; font-size: 11px; font-weight: 700; border-radius: 50%; min-width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; padding: 2px; }
        .bottom-nav { position: absolute; bottom: 0; left: 0; width: 100%; height: 60px; background: var(--surface); display: flex; border-top: 1px solid var(--border-color); z-index: 100; }
        .nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-sub); gap: 2px; cursor: pointer; font-size: 11px; }
        .nav-item.active { color: var(--text-main); font-weight: 600; }
        .nav-icon { font-size: 20px; }
        .full-screen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; height: 100dvh; background: var(--chat-bg); display: none; flex-direction: column; z-index: 9999; }
        .full-screen.active { display: flex; }
        .fs-header { background: var(--surface); color: var(--text-main); padding: 10px 16px; display: flex; align-items: center; gap: 12px; flex-shrink: 0; border-bottom: 1px solid var(--border-color); }
        .fs-title { font-size: 17px; font-weight: 600; flex: 1; color: var(--text-main); }
        .chat-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: var(--chat-bg); }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; box-shadow: 0 1px 1px rgba(0,0,0,0.1); color: var(--text-main); background: var(--bubble-recv); }
        .bubble.sent { background: var(--bubble-sent); align-self: flex-end; }
        .bubble img, .bubble video { width: 100%; border-radius: 6px; margin-top: 4px; }
        .chat-footer { background: var(--surface); padding: 8px 12px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; border-top: 1px solid var(--border-color); }
        .msg-box { flex: 1; background: var(--search-bg); border-radius: 24px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; border: 1px solid var(--border-color); }
        .msg-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        .btn-circle { background: var(--green-wa); border: none; width: 42px; height: 42px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; font-size: 18px; }
        #attachment-menu { position: fixed; bottom: 70px; left: 16px; right: 16px; background: var(--surface); border-radius: 16px; padding: 16px; display: none; grid-template-columns: repeat(3, 1fr); gap: 16px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.2); z-index: 10000; border: 1px solid var(--border-color); }
        #attachment-menu.active { display: grid; }
        .att-option { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: var(--text-main); }
        .att-icon { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    </style>
</head>
<body>
    <div id="login-modal">
        <div class="login-card">
            <h2>WhatsApp</h2>
            <p style="color: var(--text-sub); margin-bottom: 16px; font-size: 14px;">Digite seu nome para entrar:</p>
            <input type="text" id="user-name-input" placeholder="Seu nome">
            <button onclick="entrarNoApp()">Avançar</button>
        </div>
    </div>
    <div class="app-layout">
        <div class="header">
            <span class="brand">WhatsApp</span>
            <div class="header-icons">
                <span onclick="criarNovoGrupo()" title="Novo Grupo">👥➕</span>
                <span onclick="toggleTheme()" title="Mudar Tema">🌓</span>
            </div>
        </div>
        <div class="container">
            <div id="tab-chats" class="tab-content active">
                <div class="search-container">
                    <div class="search-box">
                        <span>🔍</span>
                        <input type="text" placeholder="Pesquisar conversa">
                    </div>
                </div>
                <div class="filter-bar">
                    <div class="chip active">Todas</div>
                    <div class="chip">Não lidas</div>
                    <div class="chip">Favoritos</div>
                    <div class="chip">Grupos</div>
                </div>
                <div class="chat-list" id="dynamic-chat-list">
                    <div class="chat-item" onclick="openChat('Lu', '#e91e63')">
                        <div class="avatar" style="background:#e91e63;">L</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Lu</span><span class="chat-time">6:00</span></div>
                            <div class="chat-bottom"><span class="chat-msg">ta bom</span><span class="badge">1</span></div>
                        </div>
                    </div>
                    <div class="chat-item" onclick="openChat('ITABOA NOTÍCIAS 2026', '#25d366')">
                        <div class="avatar" style="background:#25d366;">IN</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">ITABOA NOTÍCIAS 2026</span><span class="chat-time">5:35</span></div>
                            <div class="chat-bottom"><span class="chat-msg">~ Silvinho q.r.a urso 🐻: !(((</span></div>
                        </div>
                    </div>
                    <div class="chat-item" onclick="openChat('Dime', '#607d8b')">
                        <div class="avatar" style="background:#607d8b;">D</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Dime</span><span class="chat-time">Ontem</span></div>
                            <div class="chat-bottom"><span class="chat-msg">Veio ontem de moto...</span></div>
                        </div>
                    </div>
                    <div class="chat-item" onclick="openChat('Lucio Flávio', '#3f51b5')">
                        <div class="avatar" style="background:#3f51b5;">LF</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Lucio Flávio</span><span class="chat-time">Ontem</span></div>
                            <div class="chat-bottom"><span class="chat-msg">Kkk criativo né.</span><span class="badge">2</span></div>
                        </div>
                    </div>
                    <div class="chat-item" onclick="openChat('Reinaldo Goudim', '#d32f2f')">
                        <div class="avatar" style="background:#d32f2f;">RG</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Reinaldo Goudim</span><span class="chat-time">Ontem</span></div>
                            <div class="chat-bottom"><span class="chat-msg">Mensagem de voz (0:03)</span></div>
                        </div>
                    </div>
                    <div class="chat-item" onclick="openChat('micaella', '#e040fb')">
                        <div class="avatar" style="background:#e040fb;">M</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">micaella</span><span class="chat-time">Ontem</span></div>
                            <div class="chat-bottom"><span class="chat-msg">Já já acaba</span></div>
                        </div>
                    </div>
                    <div class="chat-item" onclick="openChat('FAMÍLIA GOUDIM', '#ff9800')">
                        <div class="avatar" style="background:#ff9800;">FG</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">FAMÍLIA GOUDIM 👨‍👩‍👦</span><span class="chat-time">20:15</span></div>
                            <div class="chat-bottom"><span class="chat-msg">Dirce: Boa noite</span></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="tab-status" class="tab-content" style="padding: 16px;">
                <div style="font-weight: 600; color: var(--text-sub); margin-bottom: 12px;">Status</div>
                <div class="chat-item" onclick="alert('Status publicado!')">
                    <div class="avatar" style="background:var(--green-wa);">➕</div>
                    <div class="chat-info"><div class="chat-name">Meu status</div><div class="chat-time">Toque para adicionar</div></div>
                </div>
            </div>
            <div id="tab-communities" class="tab-content" style="padding: 24px; text-align: center;">
                <h3 style="margin-bottom: 10px;">Comunidades</h3>
                <p style="color: var(--text-sub); font-size: 14px;">Organize seus grupos em comunidades.</p>
            </div>
            <div id="tab-calls" class="tab-content" style="padding: 16px;">
                <div style="font-weight: 600; color: var(--text-sub); margin-bottom: 12px;">Recentes</div>
                <div class="chat-item">
                    <div class="avatar" style="background:#607d8b;">D</div>
                    <div class="chat-info"><div class="chat-top"><span class="chat-name">Dime</span></div><div class="chat-bottom"><span class="chat-msg" style="color:var(--green-badge);">📞 Chamada de voz</span><span class="chat-time">Ontem</span></div></div>
                </div>
            </div>
        </div>
        <div class="bottom-nav">
            <div class="nav-item active" onclick="switchTab('chats', this)"><span class="nav-icon">💬</span><span>Conversas</span></div>
            <div class="nav-item" onclick="switchTab('status', this)"><span class="nav-icon">⭕</span><span>Atualizações</span></div>
            <div class="nav-item" onclick="switchTab('communities', this)"><span class="nav-icon">👥</span><span>Comunidades</span></div>
            <div class="nav-item" onclick="switchTab('calls', this)"><span class="nav-icon">📞</span><span>Ligações</span></div>
        </div>
    </div>
    <div id="chat-screen" class="full-screen">
        <div class="fs-header">
            <span onclick="closeChat()" style="cursor:pointer; font-size: 20px;">⬅️</span>
            <div class="avatar" id="active-chat-avatar" style="width:36px; height:36px; font-size:14px;"></div>
            <span class="fs-title" id="active-chat-name">Conversa</span>
        </div>
        <div class="chat-body" id="active-chat-messages"></div>
        <div id="attachment-menu">
            <div class="att-option" onclick="document.getElementById('file-img').click()"><div class="att-icon" style="background:#bf59cf;">🖼️</div><span>Foto</span></div>
            <div class="att-option" onclick="document.getElementById('file-vid').click()"><div class="att-icon" style="background:#d32f2f;">📹</div><span>Vídeo</span></div>
            <div class="att-option" onclick="enviarAudioReal()"><div class="att-icon" style="background:#00a884;">🎤</div><span>Áudio</span></div>
        </div>
        <input type="file" id="file-img" style="display:none" accept="image/*" onchange="enviarMidiaReal(event, 'image')">
        <input type="file" id="file-vid" style="display:none" accept="video/*" onchange="enviarMidiaReal(event, 'video')">
        <div class="chat-footer">
            <span style="cursor:pointer; font-size: 20px;" onclick="toggleAttachmentMenu()">📎</span>
            <div class="msg-box"><input type="text" id="chat-input-field" placeholder="Mensagem" onkeypress="if(event.key === 'Enter') enviarMensagemTexto()"></div>
            <button class="btn-circle" onclick="enviarMensagemTexto()">📤</button>
        </div>
    </div>
    <script>
        const socket = io();
        let meuNome = ''; let salaAtual = '';
        function entrarNoApp() {
            let nome = document.getElementById('user-name-input').value.trim();
            if(!nome) { alert('Digite seu nome!'); return; }
            meuNome = nome;
            document.getElementById('login-modal').style.display = 'none';
        }
        function switchTab(tab, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            element.classList.add('active');
        }
        function openChat(name, color) {
            if(!meuNome) { alert('Identifique-se primeiro.'); return; }
            salaAtual = name;
            document.getElementById('active-chat-name').innerText = name;
            let av = document.getElementById('active-chat-avatar');
            av.innerText = name.substring(0, 2).toUpperCase();
            av.style.background = color;
            document.getElementById('active-chat-messages').innerHTML = '';
            document.getElementById('chat-screen').classList.add('active');
            socket.emit('join', { username: meuNome, room: salaAtual });
        }
        function closeChat() {
            socket.emit('leave', { username: meuNome, room: salaAtual });
            document.getElementById('chat-screen').classList.remove('active');
            document.getElementById('attachment-menu').classList.remove('active');
        }
        function toggleAttachmentMenu() { document.getElementById('attachment-menu').classList.toggle('active'); }
        function criarNovoGrupo() {
            let nomeGrupo = prompt("Digite o nome do novo grupo:");
            if(nomeGrupo) {
                let lista = document.getElementById('dynamic-chat-list');
                lista.innerHTML += `<div class="chat-item" onclick="openChat('${nomeGrupo}', '#00a884')"><div class="avatar" style="background:#00a884;">👥</div><div class="chat-info"><div class="chat-top"><span class="chat-name">${nomeGrupo}</span><span class="chat-time">Agora</span></div><div class="chat-bottom"><span class="chat-msg">Grupo criado</span></div></div></div>`;
                openChat(nomeGrupo, '#00a884');
            }
        }
        function enviarMensagemTexto() {
            let input = document.getElementById('chat-input-field');
            let text = input.value.trim();
            if(!text) return;
            socket.emit('message', { room: salaAtual, username: meuNome, type: 'text', content: text });
            input.value = '';
        }
        function enviarMidiaReal(event, type) {
            let file = event.target.files[0];
            if(!file) return;
            let reader = new FileReader();
            reader.onload = function(e) { socket.emit('messa
