import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "plugadoz-secret-key"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Plugadoz</title>

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

html, body {
    width: 100%;
    height: 100%;
}

body {
    background: #111b21;
    color: #e9edef;
    overflow: hidden;
}

#login {
    position: fixed;
    inset: 0;
    z-index: 9999;

    background: #111b21;

    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    padding: 20px;
}

#login h1 {
    color: #00a884;
    margin-bottom: 10px;
}

#login p {
    color: #8696a0;
    margin-bottom: 20px;
}

#username {
    width: 100%;
    max-width: 350px;

    padding: 15px;

    border: 1px solid #2a3942;
    border-radius: 25px;

    background: #202c33;
    color: white;

    outline: none;

    font-size: 16px;

    margin-bottom: 12px;
}

#login button {
    width: 100%;
    max-width: 350px;

    padding: 15px;

    border: none;
    border-radius: 25px;

    background: #00a884;
    color: white;

    font-size: 16px;
    font-weight: bold;
}

#app {
    display: none;

    width: 100%;
    height: 100dvh;

    flex-direction: column;
}

.header {
    height: 60px;
    flex-shrink: 0;

    background: #202c33;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 16px;

    font-size: 21px;
    font-weight: bold;
}

.logo {
    color: #00a884;
}

.header button {
    border: none;
    background: transparent;
    color: #aebac1;
    font-size: 22px;
}

.filters {
    height: 50px;
    flex-shrink: 0;

    display: flex;
    gap: 8px;

    align-items: center;

    padding: 7px 12px;

    background: #111b21;

    overflow-x: auto;
}

.filter {
    padding: 7px 14px;

    border-radius: 20px;

    background: #202c33;
    color: #8696a0;

    white-space: nowrap;
}

.filter.active {
    background: #005c4b;
    color: white;
}

.content {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
}

.tab {
    display: none;
}

.tab.active {
    display: block;
}

.chat {
    display: flex;
    align-items: center;

    gap: 13px;

    padding: 11px 15px;

    border-bottom: 1px solid #1f2c34;

    cursor: pointer;
}

.avatar {
    width: 50px;
    height: 50px;

    flex-shrink: 0;

    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    background: #00a884;

    color: white;

    font-weight: bold;
}

.chat-info {
    flex: 1;
    min-width: 0;
}

.chat-name {
    font-size: 16px;
    font-weight: bold;
}

.chat-preview {
    margin-top: 4px;

    color: #8696a0;

    font-size: 14px;

    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.bottom {
    height: 64px;
    flex-shrink: 0;

    display: flex;

    border-top: 1px solid #222d34;

    background: #111b21;
}

.nav {
    flex: 1;

    display: flex;
    flex-direction: column;

    align-items: center;
    justify-content: center;

    gap: 4px;

    color: #8696a0;

    font-size: 11px;
}

.nav span:first-child {
    font-size: 20px;
}

.nav.active {
    color: #00a884;
}

#chat-screen {
    display: none;

    position: fixed;
    inset: 0;

    z-index: 10000;

    background: #0b141a;

    flex-direction: column;
}

.chat-header {
    height: 60px;
    flex-shrink: 0;

    display: flex;
    align-items: center;

    gap: 12px;

    padding: 0 12px;

    background: #202c33;
}

.back {
    font-size: 24px;
    cursor: pointer;
}

.chat-header-title {
    font-size: 17px;
    font-weight: bold;
}

.messages {
    flex: 1;
    min-height: 0;

    overflow-y: auto;

    padding: 15px;

    display: flex;
    flex-direction: column;

    gap: 7px;
}

.message-line {
    display: flex;
}

.message-line.mine {
    justify-content: flex-end;
}

.message {
    max-width: 80%;

    padding: 8px 10px;

    border-radius: 8px;

    background: #202c33;

    word-break: break-word;
}

.mine .message {
    background: #005c4b;
}

.message-user {
    color: #53bdeb;

    font-size: 12px;
    font-weight: bold;

    margin-bottom: 3px;
}

.message-time {
    color: #8696a0;

    font-size: 10px;

    margin-top: 5px;

    text-align: right;
}

.chat-footer {
    min-height: 60px;
    flex-shrink: 0;

    display: flex;
    align-items: center;

    gap: 7px;

    padding: 8px;

    background: #202c33;
}

#message {
    flex: 1;

    min-width: 0;

    padding: 12px 16px;

    border: none;
    outline: none;

    border-radius: 24px;

    background: #2a3942;
    color: white;

    font-size: 15px;
}

.send {
    width: 42px;
    height: 42px;

    border: none;

    border-radius: 50%;

    background: #00a884;

    color: white;

    font-size: 17px;
}

.empty {
    padding: 40px 20px;

    text-align: center;

    color: #8696a0;
}
</style>
</head>

<body>

<div id="login">

    <h1>Plugadoz</h1>

    <p>Seu mensageiro conectado</p>

    <input
        id="username"
        maxlength="40"
        placeholder="Digite seu nome"
        autocomplete="off"
    >

    <button onclick="entrar()">
        Entrar
    </button>

</div>


<div id="app">

    <div class="header">

        <div class="logo">
            Plugadoz
        </div>

        <button onclick="novoGrupo()">
            ＋
        </button>

    </div>


    <div class="filters">

        <div class="filter active">
            Todas
        </div>

        <div class="filter">
            Não lidas
        </div>

        <div class="filter">
            Favoritos
        </div>

        <div
            class="filter"
            onclick="novoGrupo()"
        >
            Grupos ＋
        </div>

    </div>


    <div class="content">

        <div
            id="conversas"
            class="tab active"
        >

            <div
                class="chat"
                onclick="abrirChat('Pedro Ferreira')"
            >

                <div class="avatar">
                    P
                </div>

                <div class="chat-info">

                    <div class="chat-name">
                        Pedro Ferreira
                    </div>

                    <div class="chat-preview">
                        Toque para conversar
                    </div>

                </div>

            </div>


            <div
                class="chat"
                onclick="abrirChat('ITABOA NOTÍCIAS 2026')"
            >

                <div
                    class="avatar"
                    style="background:#25d366"
                >
                    IN
                </div>

                <div class="chat-info">

                    <div class="chat-name">
                        ITABOA NOTÍCIAS 2026
                    </div>

                    <div class="chat-preview">
                        Toque para conversar
                    </div>

                </div>

            </div>


            <div
                class="chat"
                onclick="abrirChat('Lucy')"
            >

                <div
                    class="avatar"
                    style="background:#ff9800"
                >
                    L
                </div>

                <div class="chat-info">

                    <div class="chat-name">
                        Lucy
                    </div>

                    <div class="chat-preview">
                        Toque para conversar
                    </div>

                </div>

            </div>

        </div>


        <div
            id="atualizacoes"
            class="tab"
        >

            <div class="empty">

                <h3>Status</h3>

                <p style="margin-top:10px">
                    Nenhuma atualização ainda.
                </p>

                <button
                    onclick="novoStatus()"
                    style="
                        margin-top:20px;
                        padding:12px 18px;
                        border:none;
                        border-radius:20px;
                        background:#00a884;
                        color:white;
                    "
                >
                    Criar status
                </button>

            </div>

        </div>


        <div
            id="comunidades"
            class="tab"
        >

            <div class="empty">

                <h3>
                    Comunidades
                </h3>

                <p style="margin-top:10px">
                    Crie grupos para começar.
                </p>

            </div>

        </div>


        <div
            id="ligacoes"
            class="tab"
        >

            <div class="empty">

                <h3>
                    Ligações
                </h3>

                <p style="margin-top:10px">
                    Chamadas serão adicionadas.
                </p>

            </div>

        </div>

    </div>


    <div class="bottom">

        <div
            class="nav active"
            onclick="aba('conversas', this)"
        >
            <span>💬</span>
            <span>Conversas</span>
        </div>

        <div
            class="nav"
            onclick="aba('atualizacoes', this)"
        >
            <span>⭕</span>
            <span>Atualizações</span>
        </div>

        <div
            class="nav"
            onclick="aba('comunidades', this)"
        >
            <span>👥</span>
            <span>Comunidades</span>
        </div>

        <div
            class="nav"
            onclick="aba('ligacoes', this)"
        >
            <span>📞</span>
            <span>Ligações</span>
        </div>

    </div>

</div>


<div id="chat-screen">

    <div class="chat-header">

        <div
            class="back"
            onclick="fecharChat()"
        >
            ←
        </div>

        <div
            id="chat-title"
            class="chat-header-title"
        >
            Chat
        </div>

    </div>


    <div
        id="messages"
        class="messages"
    ></div>


    <div class="chat-footer">

        <input
            id="message"
            maxlength="5000"
            placeholder="Mensagem"
            autocomplete="off"
        >

        <button
            class="send"
            onclick="enviar()"
        >
            ➤
        </button>

    </div>

</div>


<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>

<script>

const socket = io();

let meuNome = "";
let salaAtual = "";


function entrar() {

    const input =
        document.getElementById("username");

    const nome =
        input.value.trim();

    if (!nome) {

        alert("Digite seu nome.");

        return;
    }

    meuNome = nome;

    document
        .getElementById("login")
        .style.display = "none";

    document
        .getElementById("app")
        .style.display = "flex";

    socket.emit(
        "login",
        {
            username: meuNome
        }
    );
}


document
    .getElementById("username")
    .addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {
                entrar();
            }

        }
    );


function aba(nome, elemento) {

    document
        .querySelectorAll(".nav")
        .forEach(function(item) {
            item.classList.remove("active");
        });

    document
        .querySelectorAll(".tab")
        .forEach(function(item) {
            item.classList.remove("active");
        });

    elemento.classList.add("active");

    document
        .getElementById(nome)
        .classList.add("active");

}


function abrirChat(nome) {

    if (!meuNome) {

        alert("Entre primeiro.");

        return;
    }

    salaAtual = nome;

    document
        .getElementById("chat-title")
        .innerText = nome;

    document
        .getElementById("messages")
        .innerHTML = "";

    document
        .getElementById("chat-screen")
        .style.display = "flex";

    socket.emit(
        "join",
        {
            room: salaAtual
        }
    );

    setTimeout(function() {

        document
            .getElementById("message")
            .focus();

    }, 100);

}


function fecharChat() {

    if (salaAtual) {

        socket.emit(
            "leave",
            {
                room: salaAtual
            }
        );

    }

    salaAtual = "";

    document
        .getElementById("chat-screen")
        .style.display = "none";

}


function enviar() {

    const input =
        document.getElementById("message");

    const texto =
        input.value.trim();

    if (!texto) {
        return;
    }

    if (!salaAtual) {
        return;
    }

    socket.emit(
        "message",
        {
            room: salaAtual,
            username: meuNome,
            type: "text",
            content: texto
        }
    );

    input.value = "";

    input.focus();

}


document
    .getElementById("message")
    .addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                enviar();

            }

        }
    );


socket.on(
    "message",
    function(data) {

        if (
            data.room !== salaAtual
        ) {
            return;
        }

        const box =
            document.getElementById(
                "messages"
            );

        const linha =
            document.createElement("div");

        linha.className =
            "message-line";

        if (
            data.username === meuNome
        ) {

            linha.classList.add("mine");

        }

        const mensagem =
            document.createElement("div");

        mensagem.className =
            "message";

        if (
            data.username !== meuNome
        ) {

            const usuario =
                document.createElement("div");

            usuario.className =
                "message-user";

            usuario.innerText =
                data.username;

            mensagem.appendChild(
                usuario
            );

        }

        const texto =
            document.createElement("div");

        texto.innerText =
            data.content;

        mensagem.appendChild(
            texto
        );

        const hora =
            document.createElement("div");

        hora.className =
            "message-time";

        hora.innerText =
            new Date().toLocaleTimeString(
                "pt-BR",
                {
                    hour: "2-digit",
                    minute: "2-digit"
                }
            );

        mensagem.appendChild(
            hora
        );

        linha.appendChild(
            mensagem
        );

        box.appendChild(
            linha
        );

        box.scrollTop =
            box.scrollHeight;

    }
);


function novoGrupo() {

    const nome =
        prompt("Nome do grupo:");

    if (!nome) {
        return;
    }

    const nomeLimpo =
        nome.trim();

    if (!nomeLimpo) {
        return;
    }

    const area =
        document.getElementById(
            "conversas"
        );

    const div =
        document.createElement("div");

    div.className =
        "chat";

    div.onclick =
        function() {
            abrirChat(nomeLimpo);
        };

    div.innerHTML = `
        <div
            class="avatar"
            style="background:#00a884"
        >
            👥
        </div>

        <div class="chat-info">

            <div class="chat-name">
                ${escapeHtml(nomeLimpo)}
            </div>

            <div class="chat-preview">
                Grupo criado
            </div>

        </div>
    `;

    area.prepend(div);

}


function novoStatus() {

    const status =
        prompt("Digite seu status:");

    if (!status) {
        return;
    }

    alert(
        "Status criado com sucesso."
    );

}


function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.innerText =
        text;

    return div.innerHTML;

}

</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@socketio.on("login")
def handle_login(data):
    username = str(
        data.get("username", "")
    ).strip()

    if username:
        emit(
            "login_ok",
            {
                "username": username
            }
        )


@socketio.on("join")
def handle_join(data):

    room = str(
        data.get("room", "")
    ).strip()

    if room:
        join_room(room)


@socketio.on("leave")
def handle_leave(data):

    room = str(
        data.get("room", "")
    ).strip()

    if room:
        leave_room(room)


@socketio.on("message")
def handle_message(data):

    room = str(
        data.get("room", "")
    ).strip()

    username = str(
        data.get("username", "")
    ).strip()

    content = str(
        data.get("content", "")
    )

    msg_type = str(
        data.get("type", "text")
    )

    if not room:
        return

    if not username:
        return

    if not content:
        return

    emit(
        "message",
        {
            "room": room,
            "username": username,
            "type": msg_type,
            "content": content
        },
        room=room
    )


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
