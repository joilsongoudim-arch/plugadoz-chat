from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WhatsApp</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">
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
            --card-bg: #f0f2f5;
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
            --card-bg: #202c33;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg-body); color: var(--text-main); }

        .app-layout { display: flex; flex-direction: column; height: 100vh; height: 100dvh; width: 100vw; position: relative; }

        /* Header Principal */
        .header { background: var(--surface); padding: 12px 16px 8px 16px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .brand { font-size: 24px; font-weight: 700; color: #00a884; font-family: sans-serif; letter-spacing: -0.5px; }
        .header-icons { display: flex; gap: 20px; color: var(--text-sub); align-items: center; }
        .header-icons .material-icons-outlined { font-size: 24px; cursor: pointer; }

        /* Container de Conteúdo & Abas */
        .container { flex: 1; overflow-y: auto; position: relative; background: var(--bg-body); padding-bottom: 80px; }
        .tab-content { display: none; height: 100%; }
        .tab-content.active { display: flex; flex-direction: column; }

        /* Search Bar */
        .search-container { padding: 4px 16px 8px 16px; }
        .search-box { background: var(--search-bg); border-radius: 24px; padding: 10px 16px; display: flex; align-items: center; gap: 12px; border: 1px solid var(--border-color); }
        .search-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        .search-box input::placeholder { color: var(--text-sub); }

        /* Chips / Filtros */
        .filter-bar { display: flex; gap: 8px; padding: 4px 16px 12px 16px; overflow-x: auto; flex-shrink: 0; align-items: center; }
        .filter-bar::-webkit-scrollbar { display: none; }
        .chip { background: var(--chip-bg); color: var(--text-sub); padding: 6px 14px; border-radius: 18px; font-size: 13px; font-weight: 500; white-space: nowrap; cursor: pointer; }
        .chip.active { background: var(--green-pill); color: var(--green-pill-text); font-weight: 600; }
        .chip-icon { background: var(--chip-bg); color: var(--text-sub); width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }

        /* Lista de Conversas */
        .chat-list { display: flex; flex-direction: column; }
        .chat-item { display: flex; align-items: center; padding: 10px 16px; gap: 14px; cursor: pointer; }
        .chat-item:active { background: var(--border-color); }
        
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; color: white; flex-shrink: 0; background-size: cover; background-position: center; }
        
        .chat-info { flex: 1; min-width: 0; }
        .chat-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px; }
        .chat-name { font-size: 16px; font-weight: 600; color: var(--text-main); }
        .chat-time { font-size: 12px; color: var(--text-sub); }
        .chat-time.highlight { color: var(--green-badge); font-weight: 600; }
        
        .chat-bottom { display: flex; justify-content: space-between; align-items: center; }
        .chat-msg { font-size: 14px; color: var(--text-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; display: flex; align-items: center; gap: 4px; }
        
        .badge { background: var(--green-badge); color: white; font-size: 11px; font-weight: 700; border-radius: 50%; min-width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; padding: 2px; }

        /* Botões Flutuantes (FABs) estilo WhatsApp */
        .meta-ai-fab {
            position: fixed; bottom: 135px; right: 16px; background: var(--surface); border: 1px solid var(--border-color);
            padding: 8px 14px; border-radius: 16px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            cursor: pointer; z-index: 10; font-size: 13px; font-weight: 600; color: var(--text-main);
        }
        .meta-ai-fab span.material-icons-outlined { color: #9c27b0; }

        .fab-main {
            position: fixed; bottom: 75px; right: 16px; width: 52px; height: 52px; border-radius: 16px;
            background: var(--green-wa); color: white; display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.25); cursor: pointer; z-index: 10;
        }

        /* Bottom Nav Bar */
        .bottom-nav { position: absolute; bottom: 0; left: 0; width: 100%; height: 60px; background: var(--surface); display: flex; border-top: 1px solid var(--border-color); z-index: 100; }
        .nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-sub); gap: 3px; cursor: pointer; }
        .nav-item.active { color: var(--text-main); font-weight: 600; }
        .nav-icon-wrapper { position: relative; width: 60px; height: 28px; border-radius: 16px; display: flex; align-items: center; justify-content: center; }
        .nav-item.active .nav-icon-wrapper { background: var(--green-pill); color: var(--green-pill-text); }
        .nav-label { font-size: 11px; }

        /* Tela de Chat Individual (Modal) */
        .full-screen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; height: 100dvh; background: var(--chat-bg); display: none; flex-direction: column; z-index: 9999; }
        .full-screen.active { display: flex; }
        .fs-header { background: var(--surface); color: var(--text-main); padding: 10px 16px; display: flex; align-items: center; gap: 12px; flex-shrink: 0; border-bottom: 1px solid var(--border-color); }
        .fs-title { font-size: 17px; font-weight: 600; flex: 1; color: var(--text-main); }
        
        .chat-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: var(--chat-bg); }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; box-shadow: 0 1px 1px rgba(0,0,0,0.1); color: var(--text-main); }
        .bubble.sent { background: var(--bubble-sent); align-self: flex-end; }
        .bubble.recv { background: var(--bubble-recv); align-self: flex-start; }
        
        .chat-footer { background: var(--surface); padding: 8px 12px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; border-top: 1px solid var(--border-color); }
        .msg-box { flex: 1; background: var(--search-bg); border-radius: 24px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; border: 1px solid var(--border-color); }
        .msg-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        
        .btn-circle { background: var(--green-wa); border: none; width: 42px; height: 42px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }

        /* Menu de Opções (3 pontinhos) */
        #options-menu { position: fixed; top: 50px; right: 16px; background: var(--menu-bg); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); display: none; flex-direction: column; z-index: 10000; width: 210px; padding: 8px 0; border: 1px solid var(--border-color); }
        #options-menu.active { display: flex; }
        .menu-item { padding: 12px 16px; font-size: 14px; color: var(--text-main); cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .menu-item:active { background: var(--border-color); }
    </style>
</head>
<body>

    <div class="app-layout">
        <!-- Header -->
        <div class="header">
            <span class="brand">WhatsApp</span>
            <div class="header-icons">
                <span class="material-icons-outlined" onclick="alert('Câmera')">photo_camera</span>
                <span class="material-icons-outlined" onclick="toggleMenu()">more_vert</span>
            </div>
        </div>

        <div class="container">
            <!-- ABA CONVERSAS -->
            <div id="tab-chats" class="tab-content active">
                <div class="search-container">
                    <div class="search-box">
                        <span class="material-icons-outlined" style="color: var(--text-sub);">search</span>
                        <input type="text" placeholder="Pergunte à Meta AI ou pesquise">
                    </div>
                </div>

                <div class="filter-bar">
                    <div class="chip active">Todas</div>
                    <div class="chip">Não lidas 3</div>
                    <div class="chip">Favoritos</div>
                    <div class="chip">Grupos</div>
                    <div class="chip-icon">+</div>
                </div>

                <div class="chat-list" id="main-chat-list">
                    <div class="chat-item" onclick="openChat('Lu', '#e91e63')">
                        <div class="avatar" style="background:#e91e63;">L</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Lu</span><span class="chat-time">6:00 da manhã</span></div>
                            <div class="chat-bottom"><span class="chat-msg">ta bom</span><span class="badge">1</span></div>
                        </div>
                    </div>

                    <div class="chat-item" onclick="openChat('ITABOA NOTÍCIAS 2026', '#25d366')">
                        <div class="avatar" style="background:#25d366;">IN</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">ITABOA NOTÍCIAS 2026</span><span class="chat-time">5:35 da madrugada</span></div>
                            <div class="chat-bottom"><span class="chat-msg">~ Silvinho q.r.a urso 🐻: !(((</span><span class="material-icons-outlined" style="font-size:16px; color:var(--text-sub);">notifications_off</span></div>
                        </div>
                    </div>

                    <div class="chat-item" onclick="openChat('Dime', '#607d8b')">
                        <div class="avatar" style="background:#607d8b;">D</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Dime</span><span class="chat-time">Ontem</span></div>
                            <div class="chat-bottom"><span class="chat-msg"><span style="color:#53bdeb;" class="material-icons-outlined" style="font-size:15px;">done_all</span> Veio ontem de moto ficou uns 40 minutos...</span></div>
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
                            <div class="chat-bottom"><span class="chat-msg"><span class="material-icons-outlined" style="font-size:16px; color:var(--green-wa);">mic</span> Mensagem de voz (0:03)</span><span class="badge">1</span></div>
                        </div>
                    </div>

                    <div class="chat-item" onclick="openChat('micaella', '#e040fb')">
                        <div class="avatar" style="background:#e040fb;">M</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">micaella</span><span class="chat-time">Ontem</span></div>
                            <div class="chat-bottom"><span class="chat-msg"><span style="color:#53bdeb;" class="material-icons-outlined" style="font-size:15px;">done_all</span> Já já acaba</span></div>
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

            <!-- OUTRAS ABAS VAZIAS OU SIMPLES -->
            <div id="tab-status" class="tab-content" style="padding: 20px; color: var(--text-sub);">Atualizações de Status</div>
            <div id="tab-communities" class="tab-content" style="padding: 20px; color: var(--text-sub);">Comunidades</div>
            <div id="tab-calls" class="tab-content" style="padding: 20px; color: var(--text-sub);">Ligações recentes</div>
        </div>

        <!-- Botões Flutuantes da Tela Inicial -->
        <div class="meta-ai-fab" onclick="alert('Meta AI')">
            <span class="material-icons-outlined">blur_on</span> Perguntar à Meta AI
        </div>
        <div class="fab-main" onclick="alert('Nova conversa')">
            <span class="material-icons-outlined">chat</span>
        </div>

        <!-- Menu Flutuante (3 pontinhos) -->
        <div id="options-menu">
            <div class="menu-item" onclick="toggleTheme(); toggleMenu();"><span id="theme-text">Modo Escuro</span></div>
            <div class="menu-item" onclick="toggleMenu()">Configurações</div>
        </div>

        <!-- Bottom Nav Bar Completa -->
        <div class="bottom-nav">
            <div class="nav-item active" onclick="switchTab('chats', this)">
                <div class="nav-icon-wrapper"><span class="material-icons-outlined">chat</span></div>
                <span class="nav-label">Conversas</span>
            </div>
            <div class="nav-item" onclick="switchTab('status', this)">
                <div class="nav-icon-wrapper"><span class="material-icons-outlined">update</span></div>
                <span class="nav-label">Atualizações</span>
            </div>
            <div class="nav-item" onclick="switchTab('communities', this)">
                <div class="nav-icon-wrapper"><span class="material-icons-outlined">groups</span></div>
                <span class="nav-label">Comunidades</span>
            </div>
            <div class="nav-item" onclick="switchTab('calls', this)">
                <div class="nav-icon-wrapper"><span class="material-icons-outlined">call</span></div>
                <span class="nav-label">Ligações</span>
            </div>
        </div>
    </div>

    <!-- Tela de Chat Individual (Modal) -->
    <div id="chat-screen" class="full-screen">
        <div class="fs-header">
            <span class="material-icons-outlined" onclick="closeChat()" style="cursor:pointer;">arrow_back</span>
            <div class="avatar" id="active-chat-avatar" style="width:36px; height:36px; font-size:14px;"></div>
            <span class="fs-title" id="active-chat-name">Conversa</span>
        </div>
        <div class="chat-body" id="active-chat-messages">
            <div class="bubble recv">Olá!</div>
        </div>
        <div class="chat-footer">
            <div class="msg-box">
                <span class="material-icons-outlined" style="color:var(--text-sub);">sentiment_satisfied</span>
                <input type="text" id="chat-input-field" placeholder="Mensagem">
                <span class="material-icons-outlined" style="color:var(--text-sub);">attach_file</span>
            </div>
            <button class="btn-circle" onclick="sendChatMessage()"><span class="material-icons-outlined">send</span></button>
        </div>
    </div>

    <script>
        function switchTab(tab, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            element.classList.add('active');
        }

        function toggleMenu() {
            document.getElementById('options-menu').classList.toggle('active');
        }

        let chatData = {};
        let activeChat = '';

        function openChat(name, color) {
            activeChat = name;
            document.getElementById('active-chat-name').innerText = name;
            let av = document.getElementById('active-chat-avatar');
            av.innerText = name.substring(0, 2).toUpperCase();
            av.style.background = color;

            let body = document.getElementById('active-chat-messages');
            body.innerHTML = `<div class="bubble recv">Histórico de conversa com ${name}</div>`;
            document.getElementById('chat-screen').classList.add('active');
        }

        function closeChat() {
            document.getElementById('chat-screen').classList.remove('active');
        }

        function sendChatMessage() {
            let input = document.getElementById('chat-input-field');
            let text = input.value.trim();
            if(!text) return;
            let body = document.getElementById('active-chat-messages');
            body.innerHTML += `<div class="bubble sent">${text}</div>`;
            input.value = '';
            body.scrollTop = body.scrollHeight;
        }

        function toggleTheme() {
            let html = document.documentElement;
            let current = html.getAttribute('data-theme');
            let next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            document.getElementById('theme-text').innerText = next === 'dark' ? 'Modo Claro' : 'Modo Escuro';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
