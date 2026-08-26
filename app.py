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

        #menu-dropdown { position: absolute; right: 10px; top: 45px; background: #233138; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: none; flex-direction: column; z-index: 2000; width: 160px; }
        .menu-item { padding: 12px 16px; color: #e9edef; font-size: 14px; cursor: pointer; }
        .menu-item:hover { background: #182229; }

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

        .bottom-nav { display: flex; background: #111b21; border-top: 1px solid #222d34; height: 60px; flex-shrink: 0; justify-content: space-around; align-items: center; }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: #8696a0; font-size: 11px; cursor: pointer; gap: 4px; flex: 1; }
        .nav-item span:first-child { font-size: 20px; }
        .nav-item.active { color: #00a884; }

        #room-screen { position: fixed; inset: 0; background: #0b141a; display: none; flex-direction: column; z-index: 1000; }
        .room-header { background: #202c33; padding: 10px 16px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: bold; border-bottom: 1px solid #222d34; flex-shrink: 0; color: #e9edef; }
        .room-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: #0b141a; }
        .bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-break: break-word; background: #202c33; color: #e9edef; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .bubble.sent { background: #005c4b; align-self: flex-end; }
        .bubble img { max-width: 100%; border-radius: 6px; margin-top: 4px; }
        
        .room-footer { background: #202c33; padding: 8px 12px; display: flex; gap: 8px; align-items: center; flex-shrink: 0; border-top: 1px solid #222d34; position: relative; }
        .input-wrapper { flex: 1; display: flex; align-items: center; background: #2a3942; border-radius: 24px; padding: 0 12px; }
        .room-footer input[type="text"] { flex: 1; background: transparent; border: none; padding: 10px 4px; color: #fff; font-size: 15px; outline: none; }
        .btn-action { background: transparent; border: none; color: #8696a0; font-size: 20px; cursor: pointer; padding: 4px; }
        .btn-send { background: #00a884; border: none; width: 40px; height: 40px; border-radius: 50%; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 16px; }
        
        #recording-panel { position: absolute; inset: 0; background: #202c33; display: none; align-items: center; justify-content: space-between; padding: 0 16px; z-index: 10; }
        .recording-timer { display: flex; align-items: center; gap: 10px; color: #ef4444; font-weight: bold; font-size: 15px; }
        .pulse-dot { width: 12px; height: 12px; background: #ef4444; border-radius: 50%; animation: pulse 1.2s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }
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
                <div class="menu-item" onclick="alert('Plugadoz v2.9 - Conectado')">Sobre</div>
            </div>
        </div>
    </div>

    <div class="filters" id="chat-filters">
        <div class="filter-chip active">Todas</div>
        <div class="filter-chip">Não lidas</div>
        <div class="filter-chip">Favoritos</div>
        <div class="filter-chip" onclick="criarGrupo()">Grupos ➕</div>
    </div>

    <div class="content-area">
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

        <div id="pane-comunidades" class="tab-pane">
            <div style="padding: 24px; text-align: center; color: #8696a0;">
                <h3>Comunidades</h3>
                <p style="font-size: 14px; margin-top: 8px;">Organize seus grupos facilmente em comunidades.</p>
            </div>
        </div>

        <div id="pane-ligacoes" class="tab-pane">
            <div style="padding: 24px; text-align: center; color: #8696a0;">
                <h3>Chamadas</h3>
                <p style="font-size: 14px; margin-top: 8px;">Toque para iniciar uma chamada de voz ou vídeo.</p>
            </div>
        </div>
    </div>

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

    <div id="room-screen">
        <div class="room-header">
            <span onclick="fecharChat()" style="cursor:pointer; font-size: 22px;">⬅️</span>
            <span id="room-title" style="flex:1;">Chat</span>
        </div>
        <div class="room-messages" id="mensagens"></div>
        
        <div class="room-footer">
            <div id="recording-panel">
                <div class="recording-timer">
                    <div class="pulse-dot"></div>
                    <span id="timer-text">0:00</span>
                </div>
                <div style="display: flex; gap: 16px; align-items: center;">
                    <span onclick="cancelarGravacao()" style="cursor:pointer; font-size: 22px;" title="Cancelar">🗑️</span>
                    <button class="btn-send" onclick="pararEEnviarAudio()" title="Enviar Áudio">➤</button>
                </div>
            </div>

            <input type="file" id="file-input" style="display:none" accept="image/*" onchange="enviarFoto(this)">
            <button class="btn-action" onclick="document.getElementById('file-input').click()" title="Enviar Foto">📎</button>
            <div class="input-wrapper">
                <input type="text" id="mensagem-input" placeholder="Mensagem" onkeypress="if(event.key==='Enter')enviarTexto()">
            </div>
            <button class="btn-action" id="btn-audio" onclick="toggleGravacao()" title="Gravar Áudio">🎤</button>
            <button class="btn-send" onclick="enviarTexto()">➤</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        let meuNome = ''; let salaAtual = '';
        let mediaRecorder; let audioChunks = [];
        let timerInterval; let segundosGravados = 0; let estaGravando = false;

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
            input.onchange = e => {};
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
            if(estaGravando) cancelarGravacao();
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

        function toggleGravacao() {
            if (!estaGravando) {
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
                        stream.getTracks().forEach(track => track.stop());
                    };

                    mediaRecorder.start();
                    estaGravando = true;
                    segundosGravados = 0;
                    document.getElementById('recording-panel').style.display = 'flex';
                    document.getElementById('timer-text').innerText = '0:00';
                    
                    timerInterval = setInterval(() => {
                        segundosGravados++;
                        let min = Math.floor(segundosGravados / 60);
                        let sec = segundosGravados % 60;
                        document.getElementById('timer-text').innerText = `${min}:${sec < 10 ? '0' : ''}${sec}`;
                    }, 1000);

                }).catch(e => alert("Permissão de microfone negada ou indisponível."));
            }
        }

        function pararEEnviarAudio() {
            if (estaGravando) {
                clearInterval(timerInterval);
                mediaRecorder.stop();
                document.getElementById('recording-panel').style.display = 'none';
                estaGravando = false;
            }
        }

        function cancelarGravacao() {
            if (estaGravando) {
                clearInterval(timerInterval);
                mediaRecorder.ondataavailable = null;
                mediaRecorder.stop();
                document.getElementById('recording-panel').style.display = 'none';
                estaGravando = false;
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
</bod
@app.get("/api/conversations/<int:cid>/messages")
def api_get_messages(cid):

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    c = db()

    if not can_access_conversation(
        c,
        u["id"],
        cid
    ):

        c.close()

        return jsonify({
            "error": "Acesso negado."
        }), 403

    rows = c.execute(
        """
        SELECT
            id,
            conversation_id,
            sender_id,
            kind,
            content,
            created_at

        FROM messages

        WHERE conversation_id = ?

        ORDER BY id ASC

        LIMIT 1000
        """,
        (cid,)
    ).fetchall()

    c.execute(
        """
        UPDATE conversation_members

        SET last_read_message_id = COALESCE(
            (
                SELECT MAX(id)
                FROM messages
                WHERE conversation_id = ?
            ),
            last_read_message_id
        )

        WHERE
            conversation_id = ?
            AND user_id = ?
        """,
        (
            cid,
            cid,
            u["id"]
        )
    )

    c.commit()

    messages = [
        serialize_message(c, row)
        for row in rows
    ]

    c.close()

    return jsonify({
        "messages": messages
    })


@app.post("/api/conversations/<int:cid>/read")
def api_read(cid):

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    c = db()

    if not can_access_conversation(
        c,
        u["id"],
        cid
    ):

        c.close()

        return jsonify({
            "error": "Acesso negado."
        }), 403

    c.execute(
        """
        UPDATE conversation_members

        SET last_read_message_id = COALESCE(
            (
                SELECT MAX(id)
                FROM messages
                WHERE conversation_id = ?
            ),
            last_read_message_id
        )

        WHERE
            conversation_id = ?
            AND user_id = ?
        """,
        (
            cid,
            cid,
            u["id"]
        )
    )

    c.commit()
    c.close()

    return jsonify({
        "ok": True
    })


@app.post("/api/conversations/<int:cid>/favorite")
def api_favorite(cid):

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    c = db()

    cv = c.execute(
        """
        SELECT kind
        FROM conversations
        WHERE id = ?
        """,
        (cid,)
    ).fetchone()

    if not cv:

        c.close()

        return jsonify({
            "error": "Conversa não encontrada."
        }), 404

    if cv["kind"] != "direct":

        c.close()

        return jsonify({
            "error":
            "Favoritos funcionam para conversas individuais."
        }), 400

    members = c.execute(
        """
        SELECT user_id

        FROM conversation_members

        WHERE conversation_id = ?
        """,
        (cid,)
    ).fetchall()

    other = next(
        (
            row["user_id"]
            for row in members
            if row["user_id"] != u["id"]
        ),
        None
    )

    if not other:

        c.close()

        return jsonify({
            "error": "Contato não encontrado."
        }), 404

    existing = c.execute(
        """
        SELECT favorite

        FROM contacts

        WHERE
            user_id = ?
            AND contact_id = ?
        """,
        (
            u["id"],
            other
        )
    ).fetchone()

    if existing:

        new_value = 0 if existing["favorite"] else 1

        c.execute(
            """
            UPDATE contacts

            SET favorite = ?

            WHERE
                user_id = ?
                AND contact_id = ?
            """,
            (
                new_value,
                u["id"],
                other
            )
        )

    else:

        new_value = 1

        c.execute(
            """
            INSERT INTO contacts (
                user_id,
                contact_id,
                favorite
            )

            VALUES (?, ?, ?)
            """,
            (
                u["id"],
                other,
                1
            )
        )

    c.commit()
    c.close()

    return jsonify({
        "favorite": bool(new_value)
    })


@app.post("/api/groups")
def api_create_group():

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    data = request.get_json(
        force=True,
        silent=True
    ) or {}

    title = str(
        data.get("title", "")
    ).strip()

    member_ids = data.get(
        "member_ids",
        []
    )

    if not isinstance(
        member_ids,
        list
    ):

        member_ids = []

    try:

        member_ids = [
            int(x)
            for x in member_ids
        ]

    except Exception:

        return jsonify({
            "error":
            "Lista de participantes inválida."
        }), 400

    member_ids = list(
        dict.fromkeys(member_ids)
    )

    member_ids = [
        x
        for x in member_ids
        if x != u["id"]
    ]

    if not title:

        return jsonify({
            "error":
            "Digite o nome do grupo."
        }), 400

    if len(title) > 80:

        return jsonify({
            "error":
            "O nome do grupo é muito grande."
        }), 400

    if len(member_ids) > 100:

        return jsonify({
            "error":
            "O grupo pode ter no máximo 100 participantes."
        }), 400

    c = db()

    if member_ids:

        placeholders = ",".join(
            "?"
            for _ in member_ids
        )

        rows = c.execute(
            f"""
            SELECT id
            FROM users
            WHERE id IN ({placeholders})
            """,
            member_ids
        ).fetchall()

        valid_ids = {
            row["id"]
            for row in rows
        }

        member_ids = [
            x
            for x in member_ids
            if x in valid_ids
        ]

    cur = c.execute(
        """
        INSERT INTO conversations (
            kind,
            title,
            created_by,
            created_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            "group",
            title,
            u["id"],
            now()
        )
    )

    cid = cur.lastrowid

    everyone = [
        u["id"]
    ] + member_ids

    c.executemany(
        """
        INSERT INTO conversation_members (
            conversation_id,
            user_id,
            joined_at
        )

        VALUES (?, ?, ?)
        """,
        [
            (
                cid,
                member_id,
                now()
            )
            for member_id in everyone
        ]
    )

    c.commit()

    payload = get_conversation_payload(
        c,
        u["id"],
        cid
    )

    c.close()

    for member_id in everyone:

        socketio.emit(
            "conversation_created",
            {
                "conversation": payload
            },
            room=f"user_{member_id}"
        )

    return jsonify({
        "conversation": payload
    })


@app.get("/api/status")
def api_status():

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    current = now()

    c = db()

    c.execute(
        """
        DELETE FROM statuses
        WHERE expires_at <= ?
        """,
        (current,)
    )

    rows = c.execute(
        """
        SELECT
            s.id,
            s.user_id,
            s.content,
            s.kind,
            s.created_at,
            s.expires_at,
            u.name,
            u.username

        FROM statuses s

        JOIN users u
        ON u.id = s.user_id

        WHERE s.expires_at > ?

        ORDER BY s.id DESC

        LIMIT 200
        """,
        (current,)
    ).fetchall()

    c.commit()
    c.close()

    return jsonify({
        "statuses": [
            {
                "id": row["id"],
                "user": {
                    "id": row["user_id"],
                    "name": row["name"],
                    "username": row["username"]
                },
                "content": row["content"],
                "kind": row["kind"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"]
            }
            for row in rows
        ]
    })


@app.post("/api/status")
def api_create_status():

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    data = request.get_json(
        force=True,
        silent=True
    ) or {}

    content = str(
        data.get("content", "")
    ).strip()

    kind = str(
        data.get("kind", "text")
    )

    if not content:

        return jsonify({
            "error":
            "O status não pode estar vazio."
        }), 400

    if len(content) > MAX_MEDIA:

        return jsonify({
            "error":
            "Status muito grande."
        }), 400

    if kind not in (
        "text",
        "image"
    ):

        kind = "text"

    created = datetime.now(
        timezone.utc
    )

    expires = created + timedelta(
        hours=24
    )

    c = db()

    cur = c.execute(
        """
        INSERT INTO statuses (
            user_id,
            content,
            kind,
            created_at,
            expires_at
        )

        VALUES (?, ?, ?, ?, ?)
        """,
        (
            u["id"],
            content,
            kind,
            created.isoformat(),
            expires.isoformat()
        )
    )

    status_id = cur.lastrowid

    c.commit()
    c.close()

    payload = {
        "id": status_id,
        "user": public_user(u),
        "content": content,
        "kind": kind,
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat()
    }

    socketio.emit(
        "new_status",
        payload
    )

    return jsonify({
        "status": payload
    })


@app.get("/api/communities")
def api_communities():

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    c = db()

    rows = c.execute(
        """
        SELECT
            c.id,
            c.name,
            c.description,
            c.created_at,
            c.owner_id,
            COUNT(cm2.user_id) AS members

        FROM communities c

        LEFT JOIN community_members cm2
        ON cm2.community_id = c.id

        WHERE EXISTS (
            SELECT 1

            FROM community_members cm

            WHERE
                cm.community_id = c.id
                AND cm.user_id = ?
        )

        GROUP BY c.id

        ORDER BY c.id DESC
        """,
        (u["id"],)
    ).fetchall()

    c.close()

    return jsonify({
        "communities": [
            dict(row)
            for row in rows
        ]
    })


@app.post("/api/communities")
def api_create_community():

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    data = request.get_json(
        force=True,
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not name:

        return jsonify({
            "error":
            "Digite o nome da comunidade."
        }), 400

    c = db()

    cur = c.execute(
        """
        INSERT INTO communities (
            name,
            description,
            owner_id,
            created_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            description,
            u["id"],
            now()
        )
    )

    community_id = cur.lastrowid

    c.execute(
        """
        INSERT INTO community_members (
            community_id,
            user_id
        )

        VALUES (?, ?)
        """,
        (
            community_id,
            u["id"]
        )
    )

    c.commit()

    row = c.execute(
        """
        SELECT
            id,
            name,
            description,
            owner_id,
            created_at

        FROM communities

        WHERE id = ?
        """,
        (community_id,)
    ).fetchone()

    c.close()

    return jsonify({
        "community": dict(row)
    })


@app.post("/api/communities/<int:community_id>/join")
def api_join_community(community_id):

    u = require_user()

    if not u:
        return jsonify({
            "error": "not_authenticated"
        }), 401

    c = db()

    community = c.execute(
        """
        SELECT id
        FROM communities
        WHERE id = ?
        """,
        (community_id,)
    ).fetchone()

    if not community:

        c.close()

        return jsonify({
            "error":
            "Comunidade não encontrada."
        }), 404

    c.execute(
        """
        INSERT OR IGNORE INTO community_members (
            community_id,
            user_id
        )

        VALUES (?, ?)
        """,
        (
            community_id,
            u["id"]
        )
    )

    c.commit()
    c.close()

    return jsonify({
        "ok": True
    })


# ============================================================
# SOCKET.IO
# ============================================================

@socketio.on("connect")
def socket_connect():

    uid = session.get("uid")

    if not uid:
        return

    join_room(
        f"user_{uid}"
    )

    socketio.emit(
        "presence",
        {
            "user_id": uid,
            "online": True
        }
    )


@socketio.on("disconnect")
def socket_disconnect():

    uid = session.get("uid")

    if not uid:
        return

    socketio.emit(
        "presence",
        {
            "user_id": uid,
            "online": False
        }
    )


@socketio.on("join_conversation")
def socket_join_conversation(data):

    uid = session.get("uid")

    if not uid:
        return

    try:
        cid = int(
            data.get("conversation_id")
        )
    except Exception:
        return

    c = db()

    allowed = can_access_conversation(
        c,
        uid,
        cid
    )

    c.close()

    if not allowed:
        return

    join_room(
        f"conversation_{cid}"
    )


@socketio.on("leave_conversation")
def socket_leave_conversation(data):

    try:
        cid = int(
            data.get("conversation_id")
        )
    except Exception:
        return

    leave_room(
        f"conversation_{cid}"
    )


@socketio.on("send_message")
def socket_send_message(data):

    uid = session.get("uid")

    if not uid:
        emit(
            "error_message",
            {
                "error":
                "Faça login novamente."
            }
        )
        return

    try:
        cid = int(
            data.get("conversation_id")
        )
    except Exception:

        emit(
            "error_message",
            {
                "error":
                "Conversa inválida."
            }
        )
        return

    kind = str(
        data.get("kind", "text")
    )

    content = str(
        data.get("content", "")
    ).strip()

    if kind not in (
        "text",
        "image",
        "audio"
    ):
        kind = "text"

    if not content:

        return

    if len(content) > MAX_MEDIA:

        emit(
            "error_message",
            {
                "error":
                "Arquivo ou mensagem muito grande."
            }
        )

        return

    c = db()

    if not can_access_conversation(
        c,
        uid,
        cid
    ):

        c.close()

        emit(
            "error_message",
            {
                "error":
                "Você não participa desta conversa."
            }
        )

        return

    cur = c.execute(
        """
        INSERT INTO messages (
            conversation_id,
            sender_id,
            kind,
            content,
            created_at
        )

        VALUES (?, ?, ?, ?, ?)
        """,
        (
            cid,
            uid,
            kind,
            content,
            now()
        )
    )

    message_id = cur.lastrowid

    row = c.execute(
        """
        SELECT
            id,
            conversation_id,
            sender_id,
            kind,
            content,
            created_at

        FROM messages

        WHERE id = ?
        """,
        (message_id,)
    ).fetchone()

    payload = serialize_message(
        c,
        row
    )

    members = c.execute(
        """
        SELECT user_id

        FROM conversation_members

        WHERE conversation_id = ?
        """,
        (cid,)
    ).fetchall()

    c.commit()
    c.close()

    socketio.emit(
        "new_message",
        payload,
        room=f"conversation_{cid}"
    )

    for member in members:

        socketio.emit(
            "conversation_changed",
            {
                "conversation_id": cid,
                "message": payload
            },
            room=f"user_{member['user_id']}"
        )


@socketio.on("typing")
def socket_typing(data):

    uid = session.get("uid")

    if not uid:
        return

    try:
        cid = int(
            data.get("conversation_id")
        )
    except Exception:
        return

    typing = bool(
        data.get("typing")
    )

    c = db()

    allowed = can_access_conversation(
        c,
        uid,
        cid
    )

    c.close()

    if not allowed:
        return

    emit(
        "typing",
        {
            "user_id": uid,
            "typing": typing
        },
        room=f"conversation_{cid}",
        include_self=False
    )


@socketio.on("call_offer")
def socket_call_offer(data):

    uid = session.get("uid")

    if not uid:
        return

    target = data.get(
        "target_user_id"
    )

    if not target:
        return

    emit(
        "call_offer",
        {
            "from_user_id": uid,
            "offer": data.get("offer")
        },
        room=f"user_{int(target)}"
    )


@socketio.on("call_answer")
def socket_call_answer(data):

    uid = session.get("uid")

    if not uid:
        return

    target = data.get(
        "target_user_id"
    )

    if not target:
        return

    emit(
        "call_answer",
        {
            "from_user_id": uid,
            "answer": data.get("answer")
        },
        room=f"user_{int(target)}"
    )


@socketio.on("ice_candidate")
def socket_ice_candidate(data):

    uid = session.get("uid")

    if not uid:
        return

    target = data.get(
        "target_user_id"
    )

    if not target:
        return

    emit(
        "ice_candidate",
        {
            "from_user_id": uid,
            "candidate": data.get(
                "candidate"
            )
        },
        room=f"user_{int(target)}"
    )


@socketio.on("call_end")
def socket_call_end(data):

    uid = session.get("uid")

    if not uid:
        return

    target = data.get(
        "target_user_id"
    )

    if not target:
        return

    emit(
        "call_end",
        {
            "from_user_id": uid
        },
        room=f"user_{int(target)}"
    )


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"
>

<title>Plugadoz</title>

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>

<style>

* {
    box-sizing:border-box;
    margin:0;
    padding:0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;
}

html,
body {
    width:100%;
    height:100%;
    overflow:hidden;
}

body {
    background:#111b21;
    color:#e9edef;
}

button,
input,
textarea {
    font:inherit;
}

button {
    cursor:pointer;
}

.hidden {
    display:none !important;
}


/* LOGIN */

#auth {
    position:fixed;
    inset:0;
    z-index:9000;
    background:#111b21;
    display:flex;
    align-items:center;
    justify-content:center;
    padding:20px;
}

.auth-card {
    width:100%;
    max-width:390px;
    background:#202c33;
    padding:30px 24px;
    border-radius:18px;
    box-shadow:0 10px 40px rgba(0,0,0,.35);
}

.logo {
    text-align:center;
    color:#00a884;
    font-size:34px;
    font-weight:800;
    margin-bottom:8px;
}

.auth-subtitle {
    text-align:center;
    color:#8696a0;
    margin-bottom:24px;
}

.auth-card input {
    width:100%;
    border:1px solid #37454d;
    outline:none;
    background:#111b21;
    color:white;
    border-radius:10px;
    padding:14px;
    margin-bottom:12px;
}

.primary {
    width:100%;
    border:0;
    background:#00a884;
    color:white;
    padding:14px;
    border-radius:10px;
    font-weight:700;
}

.auth-switch {
    text-align:center;
    margin-top:18px;
    color:#8696a0;
}

.auth-switch button {
    background:none;
    border:0;
    color:#00a884;
}


/* APP */

#app {
    width:100%;
    height:100%;
    display:flex;
    flex-direction:column;
}

.header {
    height:64px;
    flex-shrink:0;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 16px;
    background:#111b21;
}

.brand {
    color:#00a884;
    font-size:25px;
    font-weight:800;
}

.header-icons {
    display:flex;
    align-items:center;
    gap:18px;
    position:relative;
}

.icon-btn {
    background:none;
    border:0;
    color:#aebac1;
    font-size:23px;
}

.menu {
    position:absolute;
    right:0;
    top:42px;
    z-index:5000;
    width:190px;
    background:#233138;
    border-radius:8px;
    box-shadow:0 8px 30px rgba(0,0,0,.45);
    overflow:hidden;
    display:none;
}

.menu.show {
    display:block;
}

.menu button {
    display:block;
    width:100%;
    padding:14px 16px;
    border:0;
    background:none;
    color:#e9edef;
    text-align:left;
}

.menu button:hover {
    background:#182229;
}


/* FILTERS */

.filters {
    display:flex;
    gap:8px;
    padding:8px 16px;
    overflow-x:auto;
    flex-shrink:0;
}

.chip {
    border:0;
    background:#202c33;
    color:#8696a0;
    padding:8px 16px;
    border-radius:20px;
    white-space:nowrap;
}

.chip.active {
    background:#005c4b;
    color:#e9edef;
}


/* CONTENT */

.content {
    flex:1;
    min-height:0;
    overflow:auto;
}

.pane {
    display:none;
}

.pane.active {
    display:block;
}


/* CONVERSATIONS */

.search {
    padding:8px 16px;
}

.search input {
    width:100%;
    background:#202c33;
    border:0;
    outline:0;
    border-radius:10px;
    color:white;
    padding:12px 15px;
}

.chat-item {
    display:flex;
    align-items:center;
    gap:14px;
    padding:12px 16px;
    border-bottom:1px solid #1f2c34;
    cursor:pointer;
}

.chat-item:hover {
    background:#182229;
}

.avatar {
    width:50px;
    height:50px;
    border-radius:50%;
    flex-shrink:0;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#00a884;
    color:white;
    font-weight:800;
    font-size:17px;
}

.chat-info {
    min-width:0;
    flex:1;
}

.chat-top {
    display:flex;
    justify-content:space-between;
    gap:8px;
}

.chat-name {
    font-weight:700;
}

.chat-time {
    color:#8696a0;
    font-size:12px;
}

.chat-msg {
    margin-top:4px;
    color:#8696a0;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.badge {
    background:#00a884;
    color:white;
    min-width:20px;
    height:20px;
    padding:0 6px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:10px;
    font-size:11px;
}


/* BOTTOM */

.bottom {
    height:68px;
    flex-shrink:0;
    display:flex;
    border-top:1px solid #222d34;
    background:#111b21;
}

.nav {
    flex:1;
    border:0;
    background:none;
    color:#8696a0;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:3px;
}

.nav .emoji {
    font-size:22px;
}

.nav.active {
    color:#00a884;
}


/* GENERIC */

.section-title {
    padding:18px 16px 8px;
    color:#8696a0;
    text-transform:uppercase;
    font-size:12px;
    font-weight:700;
}

.center {
    text-align:center;
    padding:35px 20px;
    color:#8696a0;
}

.action-card {
    margin:12px 16px;
    padding:18px;
    border-radius:12px;
    background:#202c33;
}

.action-card button {
    margin-top:12px;
    background:#00a884;
    color:white;
    border:0;
    padding:10px 15px;
    border-radius:8px;
}


/* ROOM */

#room {
    position:fixed;
    inset:0;
    z-index:7000;
    background:#0b141a;
    display:none;
    flex-direction:column;
}

.room-head {
    height:64px;
    flex-shrink:0;
    display:flex;
    align-items:center;
    gap:12px;
    padding:8px 12px;
    background:#202c33;
}

.back {
    background:none;
    border:0;
    color:white;
    font-size:22px;
}

.room-user {
    flex:1;
}

.room-user small {
    color:#8696a0;
}

.room-tools {
    display:flex;
    gap:8px;
}

.room-tools button {
    border:0;
    background:none;
    color:#d1d7db;
    font-size:20px;
}

.messages {
    flex:1;
    min-height:0;
    overflow:auto;
    padding:16px;
    display:flex;
    flex-direction:column;
    gap:6px;
    background:#0b141a;
}

.msg {
    max-width:82%;
    align-self:flex-start;
    background:#202c33;
    border-radius:9px;
    padding:8px 10px;
    word-break:break-word;
}

.msg.me {
    align-self:flex-end;
    background:#005c4b;
}

.msg img {
    max-width:260px;
    max-height:350px;
    border-radius:7px;
    display:block;
}

.msg audio {
    max-width:240px;
}

.msg-time {
    display:block;
    color:#aebac1;
    font-size:10px;
    text-align:right;
    margin-top:4px;
}

.typing {
    min-height:20px;
    color:#00a884;
    font-size:12px;
    padding:0 16px 4px;
}

.composer {
    flex-shrink:0;
    background:#202c33;
    padding:8px;
    display:flex;
    align-items:center;
    gap:6px;
}

.composer input {
    flex:1;
    min-width:0;
    border:0;
    outline:0;
    border-radius:22px;
    background:#2a3942;
    color:white;
    padding:12px 15px;
}

.composer button {
    width:42px;
    height:42px;
    border-radius:50%;
    border:0;
    background:#00a884;
    color:white;
}

.composer .tool {
    background:none;
    color:#aebac1;
    font-size:20px;
}


/* MODAL */

.modal {
    position:fixed;
    inset:0;
    z-index:8000;
    background:rgba(0,0,0,.65);
    display:none;
    align-items:center;
    justify-content:center;
    padding:20px;
}

.modal.show {
    display:flex;
}

.modal-box {
    width:100%;
    max-width:420px;
    max-height:85vh;
    overflow:auto;
    background:#202c33;
    border-radius:14px;
    padding:20px;
}

.modal-box h3 {
    margin-bottom:15px;
}

.modal-box input,
.modal-box textarea {
    width:100%;
    background:#111b21;
    color:white;
    border:1px solid #37454d;
    border-radius:9px;
    padding:12px;
    margin-bottom:10px;
    outline:0;
}

.modal-box textarea {
    min-height:90px;
    resize:vertical;
}

.modal-actions {
    display:flex;
    gap:8px;
    justify-content:flex-end;
}

.modal-actions button {
    padding:10px 15px;
    border-radius:8px;
    border:0;
}

.cancel {
    background:#37454d;
    color:white;
}

.confirm {
    background:#00a884;
    color:white;
}


/* STATUS */

.status-item {
    display:flex;
    gap:12px;
    padding:13px 16px;
    border-bottom:1px solid #1f2c34;
    cursor:pointer;
}

.status-ring {
    border:3px solid #00a884;
    padding:2px;
    border-radius:50%;
}


/* CALL */

#call {
    position:fixed;
    inset:0;
    z-index:9500;
    background:#111b21;
    display:none;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}

#remoteVideo {
    width:100%;
    height:100%;
    object-fit:cover;
    background:#000;
}

#localVideo {
    position:absolute;
    right:15px;
    top:15px;
    width:120px;
    height:170px;
    object-fit:cover;
    border-radius:10px;
    background:#222;
}

.call-controls {
    position:absolute;
    bottom:30px;
    display:flex;
    gap:15px;
}

.call-controls button {
    width:55px;
    height:55px;
    border-radius:50%;
    border:0;
    font-size:22px;
}

.hangup {
    background:#d32f2f;
    color:white;
}


/* TOAST */

#toast {
    position:fixed;
    left:50%;
    bottom:85px;
    transform:translateX(-50%);
    background:#233138;
    color:white;
    padding:11px 16px;
    border-radius:8px;
    display:none;
    z-index:99999;
    box-shadow:0 5px 20px rgba(0,0,0,.4);
}


/* DESKTOP */

@media(min-width:800px) {

    #app {
        max-width:900px;
        margin:auto;
        border-left:1px solid #202c33;
        border-right:1px solid #202c33;
    }

}

</style>

</head>

<body>

<!-- ===================================================== -->
<!-- AUTH -->
<!-- ===================================================== -->

<div id="auth">

    <div class="auth-card">

        <div class="logo">
            Plugadoz
        </div>

        <div
            class="auth-subtitle"
            id="auth-subtitle"
        >
            Entre na sua conta
        </div>

        <div
            id="register-fields"
            class="hidden"
        >

            <input
                id="auth-name"
                placeholder="Seu nome"
                maxlength="60"
            >

        </div>

        <input
            id="auth-username"
            placeholder="Nome de usuário"
            autocomplete="username"
            maxlength="30"
        >

        <input
            id="auth-password"
            type="password"
            placeholder="Senha"
            autocomplete="current-password"
        >

        <button
            class="primary"
            id="auth-button"
            onclick="submitAuth()"
        >
            Entrar
        </button>

        <div class="auth-switch">

            <span id="switch-text">
                Ainda não tem conta?
            </span>

            <button
                onclick="toggleAuthMode()"
                id="switch-button"
            >
                Criar conta
            </button>

        </div>

    </div>

</div>


<!-- ===================================================== -->
<!-- APP -->
<!-- ===================================================== -->

<div
    id="app"
    class="hidden"
>

    <div class="header">

        <div class="brand">
            Plugadoz
        </div>

        <div class="header-icons">

            <button
                class="icon-btn"
                onclick="openCameraStatus()"
            >
                📷
            </button>

            <button
                class="icon-btn"
                onclick="toggleMenu()"
            >
                ⋮
            </button>

            <div
                id="menu"
                class="menu"
            >

                <button onclick="editProfile()">
                    Editar perfil
                </button>

                <button onclick="openGroupModal()">
                    Novo grupo
                </button>

                <button onclick="openCommunityModal()">
                    Nova comunidade
                </button>

                <button onclick="logout()">
                    Sair
                </button>

            </div>

        </div>

    </div>


    <div
        class="filters"
        id="filters"
    >

        <button
            class="chip active"
            onclick="setFilter('all',this)"
        >
            Todas
        </button>

        <button
            class="chip"
            onclick="setFilter('unread',this)"
        >
            Não lidas
        </button>

        <button
            class="chip"
            onclick="setFilter('favorite',this)"
        >
            Favoritos
        </button>

        <button
            class="chip"
            onclick="openGroupModal()"
        >
            Grupos ➕
        </button>

    </div>


    <div class="content">

        <!-- CONVERSAS -->

        <section
            id="pane-conversas"
            class="pane active"
        >

            <div class="search">

                <input
                    id="search"
                    placeholder="Pesquisar pessoas..."
                    oninput="searchUsers()"
                >

            </div>

            <div id="conversation-list"></div>

            <div
                id="search-results"
                class="hidden"
            ></div>

        </section>


        <!-- ATUALIZAÇÕES -->

        <section
            id="pane-atualizacoes"
            class="pane"
        >

            <div class="section-title">
                Meu status
            </div>

            <div
                class="status-item"
                onclick="openStatusModal()"
            >

                <div class="avatar">
                    +
                </div>

                <div class="chat-info">

                    <div class="chat-name">
                        Meu status
                    </div>

                    <div class="chat-msg">
                        Toque para adicionar uma atualização
                    </div>

                </div>

            </div>

            <div class="section-title">
                Atualizações recentes
            </div>

            <div id="status-list"></div>

        </section>


        <!-- COMUNIDADES -->

        <section
            id="pane-comunidades"
            class="pane"
        >

            <div class="center">

                <h2>
                    👥 Comunidades
                </h2>

                <p style="margin-top:10px">
                    Organize seus grupos em comunidades.
                </p>

                <button
                    class="primary"
                    style="margin-top:18px;max-width:250px"
                    onclick="openCommunityModal()"
                >
                    Criar comunidade
                </button>

            </div>

            <div id="community-list"></div>

        </section>


        <!-- LIGAÇÕES -->

        <section
            id="pane-ligacoes"
            class="pane"
        >

            <div class="center">

                <h2>
                    📞 Ligações
                </h2>

                <p style="margin-top:10px">
                    Abra uma conversa e use o telefone ou vídeo para iniciar uma chamada.
                </p>

            </div>

        </section>

    </div>


    <div class="bottom">

        <button
            class="nav active"
            onclick="changeTab('conversas',this)"
        >

            <span class="emoji">
                💬
            </span>

            <span>
                Conversas
            </span>

        </button>


        <button
            class="nav"
            onclick="changeTab('atualizacoes',this)"
        >

            <span class="emoji">
                ⭕
            </span>

            <span>
                Atualizações
            </span>

        </button>


        <button
            class="nav"
            onclick="changeTab('comunidades',this)"
        >

            <span class="emoji">
                👥
            </span>

            <span>
                Comunidades
            </span>

        </button>


        <button
            class="nav"
            onclick="changeTab('ligacoes',this)"
        >

            <span class="emoji">
                📞
            </span>

            <span>
                Ligações
            </span>

        </button>

    </div>

</div>


<!-- ===================================================== -->
<!-- ROOM -->
<!-- ===================================================== -->

<div id="room">

    <div class="room-head">

        <button
            class="back"
            onclick="closeRoom()"
        >
            ←
        </button>

        <div class="avatar" id="room-avatar">
            ?
        </div>

        <div class="room-user">

            <div id="room-title">
                Conversa
            </div>

            <small id="room-subtitle">
                online
            </small>

        </div>

        <div class="room-tools">

            <button
                onclick="startCall(false)"
                title="Ligação"
            >
                📞
            </button>

            <button
                onclick="startCall(true)"
                title="Vídeo"
            >
                📹
            </button>

            <button
                onclick="toggleFavorite()"
                title="Favorito"
            >
                ⭐
            </button>

        </div>

    </div>


    <div
        class="messages"
        id="messages"
    ></div>


    <div
        class="typing"
        id="typing"
    ></div>


    <div class="composer">

        <input
            type="file"
            id="media-input"
            accept="image/*"
            hidden
            onchange="sendImage(this)"
        >

        <button
            class="tool"
            onclick="document.getElementById('media-input').click()"
        >
            📎
        </button>

        <input
            id="message-input"
            placeholder="Mensagem"
            autocomplete="off"
            oninput="typingChanged()"
            onkeydown="messageKey(event)"
        >

        <button
            class="tool"
            id="record-button"
            onclick="toggleRecording()"
        >
            🎤
        </button>

        <button onclick="sendText()">
            ➤
        </button>

    </div>

</div>


<!-- ===================================================== -->
<!-- MODAL -->
<!-- ===================================================== -->

<div
    id="modal"
    class="modal"
>

    <div class="modal-box">

        <h3 id="modal-title">
            Título
        </h3>

        <div id="modal-content"></div>

        <div class="modal-actions">

            <button
                class="cancel"
                onclick="closeModal()"
            >
                Cancelar
            </button>

            <button
                class="confirm"
                id="modal-confirm"
            >
                Confirmar
            </button>

        </div>

    </div>

</div>


<!-- ===================================================== -->
<!-- CALL -->
<!-- ===================================================== -->

<div id="call">

    <video
        id="remoteVideo"
        autoplay
        playsinline
    ></video>

    <video
        id="localVideo"
        autoplay
        muted
        playsinline
    ></video>

    <div
        id="call-name"
        style="
            position:absolute;
            top:20px;
            left:20px;
            font-size:18px;
            font-weight:bold;
        "
    >
        Ligação
    </div>

    <div class="call-controls">

        <button
            onclick="toggleMute()"
        >
            🎤
        </button>

        <button
            onclick="toggleCamera()"
        >
            📹
        </button>

        <button
            class="hangup"
            onclick="endCall()"
        >
            ☎
        </button>

    </div>

</div>


<div id="toast"></div>


<script>

const socket = io();

let me = null;

let authMode = "login";

let conversations = [];

let currentConversation = null;

let filter = "all";

let typingTimer = null;

let mediaRecorder = null;

let audioChunks = [];

let callPeer = null;

let localStream = null;

let remoteStream = null;

let currentCallUser = null;

let callVideo = false;


/* ===================================================== */
/* UTIL */
/* ===================================================== */

function toast(text) {

    const el =
        document.getElementById("toast");

    el.textContent = text;

    el.style.display = "block";

    clearTimeout(
        window.toastTimer
    );

    window.toastTimer =
        setTimeout(
            () => {
                el.style.display = "none";
            },
            2500
        );
}


function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}


function initial(name) {

    return (
        String(name || "?")
        .trim()
        .charAt(0)
        .toUpperCase()
    );
}


function formatTime(dateString) {

    if (!dateString) {
        return "";
    }

    const d =
        new Date(dateString);

    if (isNaN(d.getTime())) {
        return "";
    }

    return d.toLocaleTimeString(
        "pt-BR",
        {
            hour:"2-digit",
            minute:"2-digit"
        }
    );
}


/* ===================================================== */
/* AUTH */
/* ===================================================== */

function toggleAuthMode() {

    authMode =
        authMode === "login"
        ? "register"
        : "login";

    document
        .getElementById("register-fields")
        .classList.toggle(
            "hidden",
            authMode !== "register"
        );

    document
        .getElementById("auth-subtitle")
        .textContent =
        authMode === "login"
        ? "Entre na sua conta"
        : "Crie sua conta no Plugadoz";

    document
        .getElementById("auth-button")
        .textContent =
        authMode === "login"
        ? "Entrar"
        : "Criar conta";

    document
        .getElementById("switch-text")
        .textContent =
        authMode === "login"
        ? "Ainda não tem conta?"
        : "Já tem uma conta?";

    document
        .getElementById("switch-button")
        .textContent =
        authMode === "login"
        ? "Criar conta"
        : "Entrar";
}


async function submitAuth() {

    const username =
        document
        .getElementById("auth-username")
        .value
        .trim();

    const password =
        document
        .getElementById("auth-password")
        .value;

    const name =
        document
        .getElementById("auth-name")
        .value
        .trim();

    if (!username || !password) {

        toast(
            "Preencha usuário e senha."
        );

        return;
    }

    if (
        authMode === "register"
        && !name
    ) {

        toast(
            "Digite seu nome."
        );

        return;
    }

    const endpoint =
        authMode === "login"
        ? "/api/login"
        : "/api/register";

    const body =
        authMode === "login"
        ? {
            username,
            password
        }
        : {
            name,
            username,
            password
        };

    try {

        const response =
            await fetch(
                endpoint,
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                            "application/json"
                    },
                    body:JSON.stringify(body)
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            toast(
                data.error ||
                "Não foi possível entrar."
            );

            return;
        }

        me =
            data.user;

        showApp();

    } catch(error) {

        toast(
            "Erro de conexão."
        );
    }
}


async function checkSession() {

    try {

        const response =
            await fetch(
                "/api/me"
            );

        if (
            response.ok
        ) {

            const data =
                await response.json();

            me =
                data.user;

            showApp();

        }

    } catch(error) {}

}


async function logout() {

    await fetch(
        "/api/logout",
        {
            method:"POST"
        }
    );

    location.reload();
}


function showApp() {

    document
        .getElementById("auth")
        .classList
        .add("hidden");

    document
        .getElementById("app")
        .classList
        .remove("hidden");

    loadConversations();

    loadStatus();

    loadCommunities();

    socket.emit(
        "join_conversation",
        {
            conversation_id: 0
        }
    );
}


/* ===================================================== */
/* MENU / PROFILE */
/* ===================================================== */

function toggleMenu() {

    document
        .getElementById("menu")
        .classList
        .toggle("show");

}


function editProfile() {

    toggleMenu();

    openModal(
        "Editar perfil",
        `
        <input
            id="profile-name"
            value="${escapeHtml(me.name)}"
            placeholder="Seu nome"
            maxlength="60"
        >
        `,
        async () => {

            const name =
                document
                .getElementById("profile-name")
                .value
                .trim();

            if (!name) {
                return;
            }

            const response =
                await fetch(
                    "/api/profile",
                    {
                        method:"PATCH",
                        headers:{
                            "Content-Type":
                                "application/json"
                        },
                        body:JSON.stringify({
                            name
                        })
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {

                toast(
                    data.error ||
                    "Erro."
                );

                return;
            }

            me =
                data.user;

            closeModal();

            toast(
                "Perfil atualizado."
            );
        }
    );
}


/* ===================================================== */
/* TABS */
/* ===================================================== */

function changeTab(tab, element) {

    document
        .querySelectorAll(".nav")
        .forEach(
            x =>
            x.classList.remove("active")
        );

    element.classList.add(
        "active"
    );

    document
        .querySelectorAll(".pane")
        .forEach(
            x =>
            x.classList.remove("active")
        );

    document
        .getElementById(
            "pane-" + tab
        )
        .classList.add("active");

    document
        .getElementById("filters")
        .style.display =
        tab === "conversas"
        ? "flex"
        : "none";
}


/* ===================================================== */
/* CONVERSATIONS */
/* ===================================================== */

async function loadConversations() {

    const response =
        await fetch(
            "/api/conversations"
        );

    if (!response.ok) {
        return;
    }

    const data =
        await response.json();

    conversations =
        data.conversations || [];

    renderConversations();
}


function renderConversations() {

    const list =
        document
        .getElementById(
            "conversation-list"
        );

    list.innerHTML = "";

    let items =
        [...conversations];

    if (filter === "unread") {

        items =
            items.filter(
                x => x.unread > 0
            );

    }

    if (filter === "favorite") {

        items =
            items.filter(
                x => x.favorite
            );

    }

    if (!items.length) {

        list.innerHTML = `
            <div class="center">
                Nenhuma conversa encontrada.
            </div>
        `;

        return;
    }

    items.forEach(
        conversation => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "chat-item";

            const title =
                conversation.title ||
                "Conversa";

            let preview =
                conversation.last
                ? conversation.last.kind === "image"
                    ? "📷 Foto"
                    : conversation.last.kind === "audio"
                        ? "🎤 Áudio"
                        : conversation.last.content
                : "Nenhuma mensagem ainda";

            if (
                conversation.last
                && conversation.last.sender_id
            ) {

                if (
                    conversation.last.sender_id === me.id
                ) {
                    preview =
                        "Você: " + preview;
                }
            }

            div.innerHTML = `
                <div class="avatar">
                    ${escapeHtml(initial(title))}
                </div>

                <div class="chat-info">

                    <div class="chat-top">

                        <span class="chat-name">
                            ${escapeHtml(title)}
                        </span>

                        <span class="chat-time">
                            ${
                                conversation.last
                                ? formatTime(
                                    conversation.last.created_at
                                )
                                : ""
                            }
                        </span>

                    </div>

                    <div class="chat-msg">
                        ${escapeHtml(preview)}
                    </div>

                </div>

                ${
                    conversation.unread
                    ? `
                    <div class="badge">
                        ${conversation.unread}
                    </div>
                    `
                    : ""
                }

            `;

            div.onclick =
                () =>
                openConversation(
                    conversation
                );

            list.appendChild(
                div
            );

        }
    );
}


function setFilter(value, element) {

    filter =
        value;

    document
        .querySelectorAll(".chip")
        .forEach(
            x =>
            x.classList.remove(
                "active"
            )
        );

    element.classList.add(
        "active"
    );

    renderConversations();
}


async function searchUsers() {

    const q =
        document
        .getElementById("search")
        .value
        .trim();

    const results =
        document
        .getElementById(
            "search-results"
        );

    if (!q) {

        results.classList.add(
            "hidden"
        );

        document
            .getElementById(
                "conversation-list"
            )
            .classList.remove(
                "hidden"
            );

        return;
    }

    const response =
        await fetch(
            "/api/users?q=" +
            encodeURIComponent(q)
        );

    if (!response.ok) {
        return;
    }

    const data =
        await response.json();

    results.innerHTML = "";

    document
        .getElementById(
            "conversation-list"
        )
        .classList.add(
            "hidden"
        );

    results.classList.remove(
        "hidden"
    );

    if (!data.users.length) {

        results.innerHTML = `
            <div class="center">
                Nenhum usuário encontrado.
            </div>
        `;

        return;
    }

    data.users.forEach(
        user => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "chat-item";

            div.innerHTML = `
                <div class="avatar">
                    ${escapeHtml(initial(user.name))}
                </div>

                <div class="chat-info">

                    <div class="chat-name">
                        ${escapeHtml(user.name)}
                    </div>

                    <div class="chat-msg">
                        @${escapeHtml(user.username)}
                    </div>

                </div>
            `;

            div.onclick =
                () =>
                startDirectChat(
                    user.id
                );

            results.appendChild(
                div
            );

        }
    );
}


async function startDirectChat(
    userId
) {

    const response =
        await fetch(
            "/api/direct/" +
            userId,
            {
                method:"POST"
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        toast(
            data.error ||
            "Erro ao abrir conversa."
        );

        return;
    }

    const conversation =
        data.conversation;

    const existing =
        conversations.find(
            x =>
            x.id === conversation.id
        );

    if (existing) {

        Object.assign(
            existing,
            conversation
        );

    } else {

        conversations.unshift(
            conversation
        );

    }

    renderConversations();

    openConversation(
        conversation
    );
}


/* ===================================================== */
/* ROOM */
/* ===================================================== */

async function openConversation(
    conversation
) {

    currentConversation =
        conversation;

    document
        .getElementById("room")
        .style.display =
        "flex";

    document
        .getElementById(
            "room-title"
        )
        .textContent =
        conversation.title;

    document
        .getElementById(
            "room-avatar"
        )
        .textContent =
        initial(
            conversation.title
        );

    document
        .getElementById(
            "room-subtitle"
        )
        .textContent =
        conversation.kind === "group"
        ? (
            conversation.members.length +
            " participantes"
        )
        : "conversa";

    socket.emit(
        "join_conversation",
        {
            conversation_id:
                conversation.id
        }
    );

    await loadMessages(
        conversation.id
    );

    await fetch(
        "/api/conversations/" +
        conversation.id +
        "/read",
        {
            method:"POST"
        }
    );

    conversation.unread = 0;

    renderConversations();

    document
        .getElementById(
            "message-input"
        )
        .focus();
}


async function loadMessages(
    conversationId
) {

    const response =
        await fetch(
            "/api/conversations/" +
            conversationId +
            "/messages"
        );

    if (!response.ok) {
        return;
    }

    const data =
        await response.json();

    const box =
        document
        .getElementById(
            "messages"
        );

    box.innerHTML = "";

    data.messages.forEach(
        renderMessage
    );

    scrollMessages();
}


function renderMessage(
    message
) {

    const box =
        document
        .getElementById(
            "messages"
        );

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "msg";

    if (
        Number(message.sender.id)
        ===
        Number(me.id)
    ) {

        div.classList.add(
            "me"
        );
    }

    let content = "";

    if (
        message.kind === "image"
    ) {

        content =
            `
            <img
                src="${message.content}"
                alt="Imagem"
            >
            `;

    } else if (
        message.kind === "audio"
    ) {

        content =
            `
            <audio
                controls
                src="${message.content}"
            ></audio>
            `;

    } else {

        content =
            escapeHtml(
                message.content
            );

    }

    div.innerHTML = `
        ${content}

        <span class="msg-time">
            ${formatTime(
                message.created_at
            )}
        </span>
    `;

    box.appendChild(
        div
    );
}


function scrollMessages() {

    const box =
        document
        .getElementById(
            "messages"
        );

    box.scrollTop =
        box.scrollHeight;
}


function closeRoom() {

    if (
        currentConversation
    ) {

        socket.emit(
            "leave_conversation",
            {
                conversation_id:
                    currentConversation.id
            }
        );

    }

    document
        .getElementById(
            "room"
        )
        .style.display =
        "none";

    currentConversation =
        null;
}


function messageKey(event) {

    if (
        event.key === "Enter"
        && !event.shiftKey
    ) {

        event.preventDefault();

        sendText();
    }
}


/* ===================================================== */
/* TEXT MESSAGE */
/* ===================================================== */

function sendText() {

    if (
        !currentConversation
    ) {
        return;
    }

    const input =
        document
        .getElementById(
            "message-input"
        );

    const content =
        input.value.trim();

    if (!content) {
        return;
    }

    socket.emit(
        "send_message",
        {
            conversation_id:
                currentConversation.id,
            kind:"text",
            content
        }
    );

    input.value = "";

    socket.emit(
        "typing",
        {
            conversation_id:
                currentConversation.id,
            typing:false
        }
    );
}


/* ===================================================== */
/* IMAGE */
/* ===================================================== */

function sendImage(
    input
) {

    if (
        !input.files ||
        !input.files[0] ||
        !currentConversation
    ) {
        return;
    }

    const file =
        input.files[0];

    if (
        file.size > 5_500_000
    ) {

        toast(
            "Imagem muito grande. Use até 5 MB."
        );

        input.value = "";

        return;
    }

    const reader =
        new FileReader();

    reader.onload =
        function() {

            socket.emit(
                "send_message",
                {
                    conversation_id:
                        currentConversation.id,
                    kind:"image",
                    content:
                        reader.result
                }
            );

        };

    reader.readAsDataURL(
        file
    );

    input.value = "";
}


/* ===================================================== */
/* AUDIO */
/* ===================================================== */

async function toggleRecording() {

    if (
        !currentConversation
    ) {
        return;
    }

    if (
        mediaRecorder
        &&
        mediaRecorder.state ===
        "recording"
    ) {

        mediaRecorder.stop();

        return;
    }

    try {

        const stream =
            await navigator
            .mediaDevices
            .getUserMedia({
                audio:true
            });

        audioChunks = [];

        mediaRecorder =
            new MediaRecorder(
                stream
            );

        mediaRecorder.ondataavailable =
            event => {

                if (
                    event.data.size
                ) {

                    audioChunks.push(
                        event.data
                    );
                }

            };

        mediaRecorder.onstop =
            () => {

                const blob =
                    new Blob(
                        audioChunks,
                        {
                            type:
                            mediaRecorder.mimeType
                            ||
                            "audio/webm"
                        }
                    );

                const reader =
                    new FileReader();

                reader.onload =
                    () => {

                        socket.emit(
                            "send_message",
                            {
                                conversation_id:
                                    currentConversation.id,
                                kind:"audio",
                                content:
                                    reader.result
                            }
                        );

                    };

                reader.readAsDataURL(
                    blob
                );

                stream
                    .getTracks()
                    .forEach(
                        track =>
                        track.stop()
                    );

                document
                    .getElementById(
                        "record-button"
                    )
                    .textContent =
                    "🎤";
            };

        mediaRecorder.start();

        document
            .getElementById(
                "record-button"
            )
            .textContent =
            "⏹";

        toast(
            "Gravando áudio..."
        );

    } catch(error) {

        toast(
            "Permita o acesso ao microfone."
        );

    }
}


/* ===================================================== */
/* TYPING */
/* ===================================================== */

function typingChanged() {

    if (
        !currentConversation
    ) {
        return;
    }

    socket.emit(
        "typing",
        {
            conversation_id:
                currentConversation.id,
            typing:true
        }
    );

    clearTimeout(
        typingTimer
    );

    typingTimer =
        setTimeout(
            () => {

                socket.emit(
                    "typing",
                    {
                        conversation_id:
                            currentConversation.id,
                        typing:false
                    }
                );

            },
            1000
        );
}


socket.on(
    "typing",
    data => {

        if (
            !currentConversation
            ||
            Number(data.user_id)
            ===
            Number(me.id)
        ) {
            return;
        }

        document
            .getElementById(
                "typing"
            )
            .textContent =
            data.typing
            ? "digitando..."
            : "";

    }
);


/* ===================================================== */
/* SOCKET MESSAGES */
/* ===================================================== */

socket.on(
    "new_message",
    message => {

        if (
            currentConversation
            &&
            Number(
                message.conversation_id
            )
            ===
            Number(
                currentConversation.id
            )
        ) {

            renderMessage(
                message
            );

            scrollMessages();

            fetch(
                "/api/conversations/" +
                currentConversation.id +
                "/read",
                {
                    method:"POST"
                }
            );

        }

        updateConversationFromMessage(
            message
        );
    }
);


function updateConversationFromMessage(
    message
) {

    let conversation =
        conversations.find(
            x =>
            Number(x.id)
            ===
            Number(
                message.conversation_id
            )
        );

    if (!conversation) {

        loadConversations();

        return;
    }

    conversation.last = {
        id:message.id,
        content:message.content,
        kind:message.kind,
        created_at:
            message.created_at,
        sender_id:
            message.sender.id
    };

    if (
        !currentConversation
        ||
        Number(
            currentConversation.id
        )
        !==
        Number(
            message.conversation_id
        )
    ) {

        if (
            Number(
                message.sender.id
            )
            !==
            Number(me.id)
        ) {

            conversation.unread =
                Number(
                    conversation.unread || 0
                ) + 1;

        }

    } else {

        conversation.unread = 0;
    }

    conversations =
        [
            conversation,
            ...conversations.filter(
                x =>
                Number(x.id)
                !==
                Number(
                    conversation.id
                )
            )
        ];

    renderConversations();
}


socket.on(
    "conversation_created",
    () => {

        loadConversations();

    }
);


socket.on(
    "conversation_changed",
    () => {

        loadConversations();

    }
);


socket.on(
    "error_message",
    data => {

        toast(
            data.error ||
            "Erro."
        );

    }
);


/* ===================================================== */
/* FAVORITE */
/* ===================================================== */

async function toggleFavorite() {

    if (
        !currentConversation
    ) {
        return;
    }

    const response =
        await fetch(
            "/api/conversations/" +
            currentConversation.id +
            "/favorite",
            {
                method:"POST"
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        toast(
            data.error ||
            "Erro."
        );

        return;
    }

    currentConversation.favorite =
        data.favorite;

    const item =
        conversations.find(
            x =>
            x.id ===
            currentConversation.id
        );

    if (item) {
        item.favorite =
            data.favorite;
    }

    renderConversations();

    toast(
        data.favorite
        ? "Adicionado aos favoritos."
        : "Removido dos favoritos."
    );
}


/* ===================================================== */
/* GROUPS */
/* ===================================================== */

function openGroupModal() {

    toggleMenu();

    openModal(
        "Novo grupo",
        `
        <input
            id="group-name"
            placeholder="Nome do grupo"
            maxlength="80"
        >

        <div
            style="
                color:#8696a0;
                margin-bottom:10px;
                font-size:13px;
            "
        >
            Digite os nomes dos participantes, separados por vírgula.
        </div>

        <input
            id="group-members"
            placeholder="Ex.: joao, maria"
        >
        `,
        createGroup
    );
}


async function createGroup() {

    const title =
        document
        .getElementById(
            "group-name"
        )
        .value
        .trim();

    const names =
        document
        .getElementById(
            "group-members"
        )
        .value
        .split(",")
        .map(
            x => x.trim()
        )
        .filter(Boolean);

    if (!title) {

        toast(
            "Digite o nome do grupo."
        );

        return;
    }

    let memberIds = [];

    for (
        const name of names
    ) {

        const response =
            await fetch(
                "/api/users?q=" +
                encodeURIComponent(name)
            );

        if (!response.ok) {
            continue;
        }

        const data =
            await response.json();

        const exact =
            data.users.find(
                x =>
                x.username.toLowerCase()
                ===
                name.toLowerCase()
                ||
                x.name.toLowerCase()
                ===
                name.toLowerCase()
            );

        if (exact) {
            memberIds.push(
                exact.id
            );
        }
    }

    const response =
        await fetch(
            "/api/groups",
            {
                method:"POST",
                headers:{
                    "Content-Type":
                        "application/json"
                },
                body:JSON.stringify({
                    title,
                    member_ids:
                        memberIds
                })
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        toast(
            data.error ||
            "Erro ao criar grupo."
        );

        return;
    }

    closeModal();

    await loadConversations();

    openConversation(
        data.conversation
    );

    toast(
        "Grupo criado."
    );
}


/* ===================================================== */
/* STATUS */
/* ===================================================== */

async function loadStatus() {

    const response =
        await fetch(
            "/api/status"
        );

    if (!response.ok) {
        return;
    }

    const data =
        await response.json();

    const list =
        document
        .getElementById(
            "status-list"
        );

    list.innerHTML = "";

    if (
        !data.statuses.length
    ) {

        list.innerHTML = `
            <div class="center">
                Nenhuma atualização ainda.
            </div>
        `;

        return;
    }

    data.statuses.forEach(
        status => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "status-item";

            div.innerHTML = `
                <div class="avatar status-ring">
                    ${escapeHtml(
                        initial(
                            status.user.name
                        )
                    )}
                </div>

                <div class="chat-info">

                    <div class="chat-top">

                        <span class="chat-name">
                            ${escapeHtml(
                                status.user.name
                            )}
                        </span>

                        <span class="chat-time">
                            ${formatTime(
                                status.created_at
                            )}
                        </span>

                    </div>

                    <div class="chat-msg">
                        ${
                            status.kind === "image"
                            ? "📷 Foto"
                            : escapeHtml(
                                status.content
                            )
                        }
                    </div>

                </div>
            `;

            div.onclick =
                () =>
                viewStatus(
                    status
                );

            list.appendChild(
                div
            );

        }
    );
}


function openStatusModal() {

    openModal(
        "Novo status",
        `
        <textarea
            id="status-text"
            maxlength="1000"
            placeholder="O que está acontecendo?"
        ></textarea>
        `,
        createStatus
    );
}


async function createStatus() {

    const content =
        document
        .getElementById(
            "status-text"
        )
        .value
        .trim();

    if (!content) {

        toast(
            "Digite seu status."
        );

        return;
    }

    const response =
        await fetch(
            "/api/status",
            {
                method:"POST",
                headers:{
                    "Content-Type":
                        "application/json"
                },
                body:JSON.stringify({
                    content,
                    kind:"text"
                })
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        toast(
            data.error ||
            "Erro."
        );

        return;
    }

    closeModal();

    loadStatus();

    toast(
        "Status publicado."
    );
}


function viewStatus(status) {

    if (
        status.kind === "image"
    ) {

        openModal(
            status.user.name,
            `
            <img
                src="${status.content}"
                style="
                    width:100%;
                    border-radius:10px;
                "
            >
            `,
            null
        );

    } else {

        openModal(
            status.user.name,
            `
            <div
                style="
                    font-size:20px;
                    line-height:1.5;
                    padding:20px 0;
                "
            >
                ${escapeHtml(
                    status.content
                )}
            </div>
            `,
            null
        );

        document
            .getElementById(
                "modal-confirm"
            )
            .classList.add(
                "hidden"
            );
    }
}


function openCameraStatus() {

    const input =
        document.createElement(
            "input"
        );

    input.type =
        "file";

    input.accept =
        "image/*";

    input.capture =
        "environment";

    input.onchange =
        async () => {

            if (
                !input.files
                ||
                !input.files[0]
            ) {
                return;
            }

            const file =
                input.files[0];

            if (
                file.size >
                5_500_000
            ) {

                toast(
                    "Imagem muito grande."
                );

                return;
            }

            const reader =
                new FileReader();

            reader.onload =
                async () => {

                    const response =
                        await fetch(
                            "/api/status",
                            {
                                method:"POST",
                                headers:{
                                    "Content-Type":
                                        "application/json"
                                },
                                body:
                                JSON.stringify({
                                    content:
                                        reader.result,
                                    kind:
                                        "image"
                                })
                            }
                        );

                    if (response.ok) {

                        loadStatus();

                        toast(
                            "Foto publicada no status."
                        );

                    }

                };

            reader.readAsDataURL(
                file
            );
        };

    input.click();
}


socket.on(
    "new_status",
    () => {

        loadStatus();

    }
);


/* ===================================================== */
/* COMMUNITIES */
/* ===================================================== */

async function loadCommunities() {

    const response =
        await fetch(
            "/api/communities"
        );

    if (!response.ok) {
        return;
    }

    const data =
        await response.json();

    const list =
        document
        .getElementById(
            "community-list"
        );

    list.innerHTML = "";

    if (
        !data.communities.length
    ) {

        list.innerHTML = `
            <div class="center">
                Você ainda não participa de nenhuma comunidade.
            </div>
        `;

        return;
    }

    data.communities.forEach(
        community => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "action-card";

            div.innerHTML = `
                <h3>
                    👥 ${escapeHtml(
                        community.name
                    )}
                </h3>

                <p
                    style="
                        color:#8696a0;
                        margin-top:6px;
                    "
                >
                    ${escapeHtml(
                        community.description ||
                        "Sem descrição."
                    )}
                </p>

                <p
                    style="
                        color:#8696a0;
                        margin-top:6px;
                    "
                >
                    ${community.members}
                    participante(s)
                </p>
            `;

            list.appendChild(
                div
            );

        }
    );
}


function openCommunityModal() {

    toggleMenu();

    openModal(
        "Nova comunidade",
        `
        <input
            id="community-name"
            placeholder="Nome da comunidade"
            maxlength="80"
        >

        <textarea
            id="community-description"
            placeholder="Descrição"
            maxlength="300"
        ></textarea>
        `,
        createCommunity
    );
}


async function createCommunity() {

    const name =
        document
        .getElementById(
            "community-name"
        )
        .value
        .trim();

    const description =
        document
        .getElementById(
            "community-description"
        )
        .value
        .trim();

    if (!name) {

        toast(
            "Digite o nome."
        );

        return;
    }

    const response =
        await fetch(
            "/api/communities",
            {
                method:"POST",
                headers:{
                    "Content-Type":
                        "application/json"
                },
                body:
                JSON.stringify({
                    name,
                    description
                })
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        toast(
            data.error ||
            "Erro."
        );

        return;
    }

    closeModal();

    loadCommunities();

    toast(
        "Comunidade criada."
    );
}


/* ===================================================== */
/* MODAL */
/* ===================================================== */

function openModal(
    title,
    content,
    confirm
) {

    document
        .getElementById(
            "modal-title"
        )
        .textContent =
        title;

    document
        .getElementById(
            "modal-content"
        )
        .innerHTML =
        content;

    const button =
        document
        .getElementById(
            "modal-confirm"
        );

    button.classList.remove(
        "hidden"
    );

    if (confirm) {

        button.onclick =
            confirm;

    } else {

        button.onclick =
            closeModal;

    }

    document
        .getElementById(
            "modal"
        )
        .classList
        .add("show");
}


function closeModal() {

    document
        .getElementById(
            "modal"
        )
        .classList
        .remove("show");
}


/* ===================================================== */
/* WEBRTC CALLS */
/* ===================================================== */

async function startCall(
    video
) {

    if (
        !currentConversation
        ||
        currentConversation.kind !==
        "direct"
    ) {

        toast(
            "Chamadas estão disponíveis em conversas individuais."
        );

        return;
    }

    const other =
        currentConversation.members.find(
            x =>
            Number(x.id)
            !==
            Number(me.id)
        );

    if (!other) {
        return;
    }

    callVideo =
        video;

    currentCallUser =
        other;

    try {

        localStream =
            await navigator
            .mediaDevices
            .getUserMedia({
                audio:true,
                video:video
            });

        document
            .getElementById(
                "localVideo"
            )
            .srcObject =
            localStream;

        document
            .getElementById(
                "call-name"
            )
            .textContent =
            "Ligando para " +
            other.name;

        document
            .getElementById(
                "call"
            )
            .style
            .display =
            "flex";

        callPeer =
            new RTCPeerConnection({
                iceServers:[
                    {
                        urls:
                        "stun:stun.l.google.com:19302"
                    },
                    {
                        urls:
                        "stun:stun1.l.google.com:19302"
                    }
                ]
            });

        remoteStream =
            new MediaStream();

        document
            .getElementById(
                "remoteVideo"
            )
            .srcObject =
            remoteStream;

        localStream
            .getTracks()
            .forEach(
                track =>
                callPeer.addTrack(
                    track,
                    localStream
                )
            );

        callPeer.ontrack =
            event => {

                event.streams[0]
                    .getTracks()
                    .forEach(
                        track =>
                        remoteStream.addTrack(
                            track
                        )
                    );

            };

        callPeer.onicecandidate =
            event => {

                if (
                    event.candidate
                ) {

                    socket.emit(
                        "ice_candidate",
                        {
                            target_user_id:
                                other.id,
                            candidate:
                                event.candidate
                        }
                    );

                }

            };

        const offer =
            await callPeer
            .createOffer();

        await callPeer
            .setLocalDescription(
                offer
            );

        socket.emit(
            "call_offer",
            {
                target_user_id:
                    other.id,
                offer
            }
        );

    } catch(error) {

        toast(
            "Não foi possível iniciar a chamada. Verifique câmera e microfone."
        );

        cleanupCall();

    }
}


socket.on(
    "call_offer",
    async data => {

        if (!me) {
            return;
        }

        const accept =
            confirm(
                "Receber chamada?"
            );

        if (!accept) {

            socket.emit(
                "call_end",
                {
                    target_user_id:
                        data.from_user_id
                }
            );

            return;
        }

        try {

            currentCallUser = {
                id:
                    data.from_user_id,
                name:
                    "Usuário"
            };

            callVideo =
                true;

            localStream =
                await navigator
                .mediaDevices
                .getUserMedia({
                    audio:true,
                    video:true
                });

            document
                .getElementById(
                    "localVideo"
                )
                .srcObject =
                localStream;

            document
                .getElementById(
                    "call"
                )
                .style
                .display =
                "flex";

            callPeer =
                new RTCPeerConnection({
                    iceServers:[
                        {
                            urls:
                            "stun:stun.l.google.com:19302"
                        },
                        {
                            urls:
                            "stun:stun1.l.google.com:19302"
                        }
                    ]
                });

            remoteStream =
                new MediaStream();

            document
                .getElementById(
                    "remoteVideo"
                )
                .srcObject =
                remoteStream;

            localStream
                .getTracks()
                .forEach(
                    track =>
                    callPeer.addTrack(
                        track,
                        localStream
                    )
                );

            callPeer.ontrack =
                event => {

                    event.streams[0]
                        .getTracks()
                        .forEach(
                            track =>
                            remoteStream.addTrack(
                                track
                            )
                        );

                };

            callPeer.onicecandidate =
                event => {

                    if (
                        event.candidate
                    ) {

                        socket.emit(
                            "ice_candidate",
                            {
                                target_user_id:
                                    data.from_user_id,
                                candidate:
                                    event.candidate
                            }
                        );

                    }

                };

            await callPeer
                .setRemoteDescription(
                    data.offer
                );

            const answer =
                await callPeer
                .createAnswer();

            await callPeer
                .setLocalDescription(
                    answer
                );

            socket.emit(
                "call_answer",
                {
                    target_user_id:
                        data.from_user_id,
                    answer
                }
            );

        } catch(error) {

            cleanupCall();

            toast(
                "Não foi possível atender a chamada."
            );
        }

    }
);


socket.on(
    "call_answer",
    async data => {

        if (
            callPeer
        ) {

            await callPeer
                .setRemoteDescription(
                    data.answer
                );

            document
                .getElementById(
                    "call-name"
                )
                .textContent =
                "Conectado";
        }

    }
);


socket.on(
    "ice_candidate",
    async data => {

        if (
            callPeer
            &&
            data.candidate
        ) {

            try {

                await callPeer
                    .addIceCandidate(
                        data.candidate
                    );

            } catch(error) {}

        }

    }
);


socket.on(
    "call_end",
    () => {

        toast(
            "A chamada terminou."
        );

        cleanupCall();

    }
);


function toggleMute() {

    if (!localStream) {
        return;
    }

    localStream
        .getAudioTracks()
        .forEach(
            track =>
            track.enabled =
            !track.enabled
        );
}


function toggleCamera() {

    if (!localStream) {
        return;
    }

    localStream
        .getVideoTracks()
        .forEach(
            track =>
            track.enabled =
            !track.enabled
        );
}


function endCall() {

    if (
        currentCallUser
    ) {

        socket.emit(
            "call_end",
            {
                target_user_id:
                    currentCallUser.id
            }
        );

    }

    cleanupCall();
}


function cleanupCall() {

    if (callPeer) {

        callPeer.close();

        callPeer =
            null;
    }

    if (localStream) {

        localStream
            .getTracks()
            .forEach(
                track =>
                track.stop()
            );

        localStream =
            null;
    }

    remoteStream =
        null;

    currentCallUser =
        null;

    document
        .getElementById(
            "remoteVideo"
        )
        .srcObject =
        null;

    document
        .getElementById(
            "localVideo"
        )
        .srcObject =
        null;

    document
        .getElementById(
            "call"
        )
        .style
        .display =
        "none";
}


/* ===================================================== */
/* CAMERA */
/* ===================================================== */

function openCameraStatus() {

    const input =
        document.createElement(
            "input"
        );

    input.type =
        "file";

    input.accept =
        "image/*";

    input.capture =
        "environment";

    input.onchange =
        async () => {

            if (
                !input.files
                ||
                !input.files[0]
            ) {
                return;
            }

            const file =
                input.files[0];

            const reader =
                new FileReader();

            reader.onload =
                async () => {

                    const response =
                        await fetch(
                            "/api/status",
                            {
                                method:"POST",
                                headers:{
                                    "Content-Type":
                                        "application/json"
                                },
                                body:
                                JSON.stringify({
                                    content:
                                        reader.result,
                                    kind:
                                        "image"
                                })
                            }
                        );

                    if (
                        response.ok
                    ) {

                        changeTab(
                            "atualizacoes",
                            document
                                .querySelectorAll(
                                    ".nav"
                                )[1]
                        );

                        loadStatus();

                        toast(
                            "Foto publicada."
                        );

                    } else {

                        toast(
                            "Não foi possível publicar."
                        );

                    }

                };

            reader.readAsDataURL(
                file
            );
        };

    input.click();
}


/* ===================================================== */
/* PROFILE UPDATE FROM SOCKET */
/* ===================================================== */

socket.on(
    "profile_updated",
    data => {

        if (
            data.user
            &&
            Number(data.user.id)
            ===
            Number(me?.id)
        ) {

            me =
                data.user;

        }

    }
);


/* ===================================================== */
/* START */
/* ===================================================== */

document.addEventListener(
    "click",
    event => {

        const menu =
            document
            .getElementById(
                "menu"
            );

        if (
            menu.classList.contains(
                "show"
            )
            &&
            !event.target.closest(
                ".header-icons"
            )
        ) {

            menu.classList.remove(
                "show"
            );

        }

    }
);


document
    .getElementById(
        "auth-password"
    )
    .addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
            ) {

                submitAuth();

            }

        }
    );


checkSession();

</script>

</body>

</html>
"""


# ============================================================
# START
# ============================================================

init_db()


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        allow_unsafe_werkzeug=True
    )
