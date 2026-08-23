from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Plugadoz</title>
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

        .app-layout { display: flex; flex-direction: column; height: 100vh; height: 100dvh; width: 100vw; }

        /* Header Principal */
        .header { background: var(--surface); padding: 12px 16px 8px 16px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .brand { font-size: 22px; font-weight: 700; color: var(--green-wa); font-family: sans-serif; letter-spacing: -0.5px; }
        .header-icons { display: flex; gap: 20px; color: var(--text-sub); align-items: center; }
        .header-icons .material-icons-outlined { font-size: 24px; cursor: pointer; }

        /* Container de Conteúdo & Abas */
        .container { flex: 1; overflow-y: auto; position: relative; background: var(--bg-body); }
        .tab-content { display: none; height: 100%; }
        .tab-content.active { display: flex; flex-direction: column; }

        /* Search Bar Meta AI Style */
        .search-container { padding: 4px 16px 8px 16px; }
        .search-box { background: var(--search-bg); border-radius: 24px; padding: 10px 16px; display: flex; align-items: center; gap: 12px; border: 1px solid var(--border-color); }
        .search-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        .search-box input::placeholder { color: var(--text-sub); }

        /* Chips / Filtros */
        .filter-bar { display: flex; gap: 8px; padding: 4px 16px 12px 16px; overflow-x: auto; flex-shrink: 0; }
        .filter-bar::-webkit-scrollbar { display: none; }
        .chip { background: var(--chip-bg); color: var(--text-sub); padding: 6px 14px; border-radius: 18px; font-size: 13px; font-weight: 500; white-space: nowrap; cursor: pointer; }
        .chip.active { background: var(--green-pill); color: var(--green-pill-text); font-weight: 600; }

        /* Lista de Conversas / Grupos */
        .chat-list { display: flex; flex-direction: column; }
        .chat-item { display: flex; align-items: center; padding: 12px 16px; gap: 14px; cursor: pointer; }
        .chat-item:active { background: var(--border-color); }
        
        .avatar { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; color: white; flex-shrink: 0; }
        
        .chat-info { flex: 1; min-width: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }
        .chat-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .chat-name { font-size: 16px; font-weight: 700; color: var(--text-main); }
        .chat-time { font-size: 12px; color: var(--text-sub); }
        .chat-time.highlight { color: var(--green-badge); font-weight: 600; }
        
        .chat-bottom { display: flex; justify-content: space-between; align-items: center; }
        .chat-msg { font-size: 14px; color: var(--text-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
        
        .badge { background: var(--green-badge); color: white; font-size: 11px; font-weight: 700; border-radius: 50%; min-width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; padding: 2px; }

        /* Atualizações (Status & Canais) */
        .status-section-title { font-size: 20px; font-weight: 700; padding: 12px 16px 8px 16px; color: var(--text-main); }
        
        .status-carousel { display: flex; gap: 10px; padding: 4px 16px 12px 16px; overflow-x: auto; flex-shrink: 0; }
        .status-carousel::-webkit-scrollbar { display: none; }
        
        .status-card {
            width: 100px; height: 160px; border-radius: 16px; flex-shrink: 0; position: relative;
            overflow: hidden; background: var(--card-bg); border: 1px solid var(--border-color); cursor: pointer;
            display: flex; flex-direction: column; justify-content: flex-end; padding: 10px;
        }
        .status-card.my-status { background: var(--card-bg); justify-content: space-between; align-items: center; padding: 12px 8px; text-align: center; }
        .status-card-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(to bottom, rgba(0,0,0,0.2) 30%, rgba(0,0,0,0.7) 100%); }
        
        .status-avatar-wrapper { position: relative; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 2; }
        .status-card.has-story .status-avatar-wrapper { border: 2.5px solid var(--green-badge); border-radius: 50%; padding: 2px; }
        .status-mini-avatar { width: 100%; height: 100%; border-radius: 50%; background: var(--green-wa); color: white; font-weight: bold; font-size: 14px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        
        .status-card-name { font-size: 12px; font-weight: 600; color: white; z-index: 2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; text-align: center; }
        .status-card.my-status .status-card-name { color: var(--text-main); font-size: 13px; }
        .add-icon-badge { position: absolute; bottom: 0; right: 0; background: var(--green-badge); color: white; width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid var(--surface); z-index: 3; }

        /* Canais */
        .channels-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 16px 8px 16px; }
        .channels-title { font-size: 20px; font-weight: 700; color: var(--text-main); }
        .btn-discover { background: var(--search-bg); border: 1px solid var(--border-color); padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 600; color: var(--text-main); cursor: pointer; }
        
        .channel-item { display: flex; align-items: center; padding: 10px 16px; gap: 14px; cursor: pointer; }
        .channel-item:active { background: var(--border-color); }
        .channel-avatar { width: 48px; height: 48px; border-radius: 50%; background: var(--card-bg); display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; font-size: 20px; border: 1px solid var(--border-color); }
        .channel-info { flex: 1; min-width: 0; }
        .channel-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
        .channel-name { font-size: 16px; font-weight: 600; color: var(--text-main); }
        .channel-time { font-size: 12px; color: var(--text-sub); }
        .channel-msg { font-size: 14px; color: var(--text-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 220px; }
        .channel-badge { background: var(--green-badge); color: white; font-size: 11px; font-weight: 700; border-radius: 50%; min-width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; padding: 0 4px; }

        /* Botões Flutuantes (FABs) */
        .fab-group { position: fixed; bottom: 72px; right: 16px; display: flex; flex-direction: column; gap: 12px; align-items: center; z-index: 10; }
        .fab-sub { width: 40px; height: 40px; border-radius: 12px; background: var(--card-bg); color: var(--text-sub); display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); cursor: pointer; border: 1px solid var(--border-color); }
        .fab-main { width: 56px; height: 56px; border-radius: 18px; background: var(--green-wa); color: white; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.2); cursor: pointer; }

        /* Bottom Nav Bar */
        .bottom-nav { height: 62px; background: var(--surface); display: flex; border-top: 1px solid var(--border-color); flex-shrink: 0; z-index: 100; }
        .nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-sub); gap: 3px; cursor: pointer; }
        .nav-item.active { color: var(--text-main); font-weight: 700; }
        .nav-icon-wrapper { position: relative; width: 50px; height: 28px; border-radius: 16px; display: flex; align-items: center; justify-content: center; }
        .nav-item.active .nav-icon-wrapper { background: var(--green-pill); color: var(--green-pill-text); }
        .nav-label { font-size: 12px; }

        /* Modais de Tela Cheia */
        .full-screen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; height: 100dvh; background: var(--chat-bg); display: none; flex-direction: column; z-index: 9999; }
        .full-screen.active { display: flex; }
        .fs-header { background: var(--surface); color: var(--text-main); padding: 12px 16px; display: flex; align-items: center; gap: 16px; flex-shrink: 0; border-bottom: 1px solid var(--border-color); }
        .fs-title { font-size: 18px; font-weight: 600; flex: 1; color: var(--text-main); }
        
        .chat-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: var(--chat-bg); }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; box-shadow: 0 1px 1px rgba(0,0,0,0.1); color: var(--text-main); }
        .bubble.sent { background: var(--bubble-sent); align-self: flex-end; }
        .bubble.recv { background: var(--bubble-recv); align-self: flex-start; }
        
        .chat-footer { background: var(--surface); padding: 8px 12px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; border-top: 1px solid var(--border-color); }
        .msg-box { flex: 1; background: var(--search-bg); border-radius: 24px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; border: 1px solid var(--border-color); }
        .msg-box input { background: transparent; border: none; outline: none; width: 100%; font-size: 15px; color: var(--text-main); }
        
        .btn-circle { background: var(--green-wa); border: none; width: 42px; height: 42px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
        .btn-circle.recording { background: #ea4335; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }

        /* Menu de Opções (3 pontinhos) */
        #options-menu { position: fixed; top: 50px; right: 16px; background: var(--menu-bg); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); display: none; flex-direction: column; z-index: 10000; width: 200px; padding: 8px 0; border: 1px solid var(--border-color); }
        #options-menu.active { display: flex; }
        .menu-item { padding: 12px 16px; font-size: 14px; color: var(--text-main); cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .menu-item:active { background: var(--border-color); }

        /* Tela de Perfil */
        #profile-screen { background: var(--bg-body); }
        .profile-content { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 20px; overflow-y: auto; }
        .profile-pic-container { width: 120px; height: 120px; border-radius: 50%; background: var(--green-wa); color: white; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: bold; position: relative; }
        .profile-card { background: var(--surface); width: 100%; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 8px; border: 1px solid var(--border-color); }
        .profile-label { font-size: 13px; color: var(--text-sub); }
        .profile-input { border: none; border-bottom: 2px solid var(--green-wa); font-size: 16px; padding: 4px 0; outline: none; width: 100%; color: var(--text-main); background: transparent; }

        /* Status Viewer */
        #status-viewer { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; height: 100dvh; background: #000; z-index: 9999; display: none; flex-direction: column; }
        #status-viewer.active { display: flex; }
        .status-progress-container { position: absolute; top: 12px; left: 12px; right: 12px; height: 2px; background: rgba(255,255,255,0.3); z-index: 10; display: flex; gap: 4px; }
        .status-bar { flex: 1; background: rgba(255,255,255,0.3); border-radius: 2px; overflow: hidden; }
        .status-fill { height: 100%; background: #fff; width: 0%; }
        .status-header { position: absolute; top: 24px; left: 12px; display: flex; align-items: center; gap: 10px; color: white; z-index: 10; width: 100%; }
        .status-content-area { flex: 1; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; text-align: center; padding: 20px; font-weight: 500; }
    </style>
</head>
<body>

    <div class="app-layout">
        <!-- Header -->
        <div class="header">
            <span class="brand" id="brand-title">Plugadoz</span>
            <div class="header-icons">
                <span class="material-icons-outlined" onclick="document.getElementById('file-status-upload').click()">photo_camera</span>
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
                    <div class="chip">Não lidas 1</div>
                    <div class="chip">Favoritos</div>
                    <div class="chip">Grupos 1</div>
                </div>

                <div class="chat-list" id="main-chat-list">
                    <div class="chat-item" onclick="openChat('Terreno', '#009688')">
                        <div class="avatar" style="background:#009688;">TE</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">Terreno</span><span class="chat-time">Agora</span></div>
                            <div class="chat-bottom"><span class="chat-msg">Oi</span></div>
                        </div>
                    </div>

                    <div class="chat-item" onclick="openChat('ITABOA NOTÍCIAS 2026', '#25d366')">
                        <div class="avatar" style="background:#25d366;">IN</div>
                        <div class="chat-info">
                            <div class="chat-top"><span class="chat-name">ITABOA NOTÍCIAS 2026</span><span class="chat-time highlight">5:38</span></div>
                            <div class="chat-bottom"><span class="chat-msg">~ Cunhado 99 @: Bom dia</span><span class="badge">1</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ABA ATUALIZAÇÕES -->
            <div id="tab-status" class="tab-content">
                <div class="status-section-title">Status</div>
                
                <div class="status-carousel" id="status-carousel-container">
                    <div class="status-card my-status" onclick="document.getElementById('file-status-upload').click()">
                        <div class="status-avatar-wrapper">
                            <div class="status-mini-avatar" id="my-status-avatar" style="background:#008069;">PL</div>
                            <div class="add-icon-badge">+</div>
                        </div>
                        <span class="status-card-name">Adicionar status</span>
                    </div>

                    <div class="status-card has-story" onclick="openStatusViewer('Lu', 'O que fizesse na vida...')">
                        <div class="status-card-overlay"></div>
                        <div class="status-avatar-wrapper">
                            <div class="status-mini-avatar" style="background:#9c27b0;">L</div>
                        </div>
                        <span class="status-card-name">Lu</span>
                    </div>

                    <div class="status-card has-story" onclick="openStatusViewer('zigoudim', 'Curtindo o fim de semana!')">
                        <div class="status-card-overlay"></div>
                        <div class="status-avatar-wrapper">
                            <div class="status-mini-avatar" style="background:#ff9800;">Z</div>
                        </div>
                        <span class="status-card-name">zigoudim</span>
                    </div>
                </div>

                <div class="channels-header">
                    <span class="channels-title">Canais</span>
                    <button class="btn-discover" onclick="alert('Explorar canais')">Descobrir</button>
                </div>

                <div class="channel-item" onclick="openChat('Olympics', '#0056b3')">
                    <div class="channel-avatar" style="color:#0056b3;">🏅</div>
                    <div class="channel-info">
                        <div class="channel-top"><span class="channel-name">Olympics</span><span class="channel-time">6:45</span></div>
                        <div class="channel-top"><span class="channel-msg">The current men's pole vault...</span><span class="channel-badge">4</span></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Menu Flutuante de Opções (3 pontinhos) com opção de Tema -->
        <div id="options-menu">
            <div class="menu-item" onclick="openNewGroupScreen(); toggleMenu();">Novo grupo</div>
            <div class="menu-item" onclick="openProfileScreen(); toggleMenu();">Configurações</div>
            <div class="menu-item" onclick="toggleTheme(); toggleMenu();"><span id="theme-menu-text">Modo Escuro</span></div>
        </div>

        <!-- Bottom Nav -->
        <div class="bottom-nav">
            <div class="nav-item active" onclick="switchTab('chats', this)">
                <div class="nav-icon-wrapper"><span class="material-icons-outlined">chat</span></div>
                <span class="nav-label">Conversas</span>
            </div>
            <div class="nav-item" onclick="switchTab('status', this)">
                <div class="nav-icon-wrapper"><span class="material-icons-outlined">update</span></div>
                <span class="nav-label">Atualizações</span>
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
            <div class="bubble recv">Olá! Tudo bem?</div>
        </div>
        <div class="chat-footer">
            <div class="msg-box">
                <span class="material-icons-outlined" style="color:var(--text-sub);">sentiment_satisfied</span>
                <input type="text" id="chat-input-field" placeholder="Mensagem">
                <span class="material-icons-outlined" style="color:var(--text-sub);">attach_file</span>
            </div>
            <button class="btn-circle" id="send-btn" onclick="sendChatMessage()"><span class="material-icons-outlined" id="send-icon">send</span></button>
        </div>
    </div>

    <!-- Tela de Perfil (Modal) -->
    <div id="profile-screen" class="full-screen">
        <div class="fs-header">
            <span class="material-icons-outlined" onclick="closeProfileScreen()" style="cursor:pointer;">arrow_back</span>
            <span class="fs-title">Configurações</span>
        </div>
        <div class="profile-content">
            <div class="profile-pic-container" id="profile-big-avatar">PL</div>
            <div class="profile-card">
                <span class="profile-label">Nome de Exibição</span>
                <input type="text" class="profile-input" id="profile-name-input" value="Plugadoz" oninput="updateProfileName(this.value)">
            </div>
        </div>
    </div>

    <!-- Status Viewer Modal -->
    <div id="status-viewer" onclick="closeStatusViewer()">
        <div class="status-progress-container">
            <div class="status-bar"><div class="status-fill" id="status-fill-anim"></div></div>
        </div>
        <div class="status-header" onclick="event.stopPropagation()">
            <div class="avatar" id="status-view-avatar" style="width:36px; height:36px; font-size:14px; background:#ff9800;">Z</div>
            <span style="font-weight:600; font-size:15px;" id="status-view-name">zigoudim</span>
        </div>
        <div class="status-content-area" id="status-view-text" onclick="event.stopPropagation()">
            Curtindo o fim de semana!
        </div>
    </div>

    <input type="file" id="file-status-upload" style="display:none" accept="image/*" onchange="handleStatusUpload(this)">

    <script>
        let currentTab = 'chats';
        function switchTab(tab, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            element.classList.add('active');
            currentTab = tab;
        }

        function toggleMenu() {
            document.getElementById('options-menu').classList.toggle('active');
        }

        window.onclick = function(event) {
            if (!event.target.closest('.header-icons') && !event.target.closest('#options-menu')) {
                document.getElementById('options-menu').classList.remove('active');
            }
        }

        let chatsData = {
            'Terreno': [{ sender: 'recv', text: 'Oi' }],
            'ITABOA NOTÍCIAS 2026': [{ sender: 'recv', text: '~ Cunhado 99 @: Bom dia' }],
            'Olympics': [{ sender: 'recv', text: "The current men's pole vault..." }]
        };
        let activeChatKey = '';

        function openChat(name, color) {
            activeChatKey = name;
            document.getElementById('active-chat-name').innerText = name;
            let av = document.getElementById('active-chat-avatar');
            av.innerText = name.substring(0, 2).toUpperCase();
            av.style.background = color;

            let body = document.getElementById('active-chat-messages');
            body.innerHTML = '';
            if(!chatsData[name]) chatsData[name] = [{sender: 'recv', text: 'Olá!'}];
            
            chatsData[name].forEach(msg => {
                body.innerHTML += `<div class="bubble ${msg.sender}">${msg.text}</div>`;
            });

            document.getElementById('chat-screen').classList.add('active');
            body.scrollTop = body.scrollHeight;
        }

        function closeChat() {
            document.getElementById('chat-screen').classList.remove('active');
        }

        function sendChatMessage() {
            let input = document.getElementById('chat-input-field');
            let text = input.value.trim();
            if(!text) return;

            if(!chatsData[activeChatKey]) chatsData[activeChatKey] = [];
            chatsData[activeChatKey].push({sender: 'sent', text: text});

            let body = document.getElementById('active-chat-messages');
            body.innerHTML += `<div class="bubble sent">${text}</div>`;
            input.value = '';
            body.scrollTop = body.scrollHeight;
        }

        document.getElementById('chat-input-field').addEventListener('keypress', function(e) {
            if(e.key === 'Enter') sendChatMessage();
        });

        function toggleTheme() {
            let html = document.documentElement;
            let current = html.getAttribute('data-theme');
            let next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            document.getElementById('theme-menu-text').innerText = next === 'dark' ? 'Modo Claro' : 'Modo Escuro';
        }

        function openProfileScreen() { document.getElementById('profile-screen').classList.add('active'); }
        function closeProfileScreen() { document.getElementById('profile-screen').classList.remove('active'); }

        function updateProfileName(val) {
            document.getElementById('brand-title').innerText = val || 'Plugadoz';
            document.getElementById('my-status-avatar').innerText = (val || 'PL').substring(0,2).toUpperCase();
            document.getElementById('profile-big-avatar').innerText = (val || 'PL').substring(0,2).toUpperCase();
        }

        function openNewGroupScreen() { alert("Criar novo grupo - Funcionalidade em desenvolvimento"); }

        let statusTimer;
        function openStatusViewer(name, text) {
            document.getElementById('status-view-name').innerText = name;
            document.getElementById('status-view-text').innerText = text;
            document.getElementById('status-view-avatar').innerText = name.substring(0,2).toUpperCase();
            
            let viewer = document.getElementById('status-viewer');
            viewer.classList.add('active');

            let fill = document.getElementById('status-fill-anim');
            fill.style.transition = 'none';
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.transition = 'width 4s linear';
                fill.style.width = '100%';
            }, 50);

            statusTimer = setTimeout(() => {
                closeStatusViewer();
            }, 4000);
        }

        function closeStatusViewer() {
            document.getElementById('status-viewer').classList.remove('active');
            clearTimeout(statusTimer);
        }

        function handleStatusUpload(input) {
            if(input.files && input.files[0]) {
                alert("Status carregado com sucesso!");
            }
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
