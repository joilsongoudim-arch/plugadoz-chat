import os
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key-2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# Interface Completa do Plugadoz integrada no arquivo único
APP_HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlugaDoz</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background-color: #111b21; color: #e9edef; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .app-container { width: 100%; max-width: 480px; height: 100%; background: #222d34; display: flex; flex-direction: column; }
        @media (min-width: 768px) { .app-container { height: 85vh; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); } }
        .header { background: #202c33; padding: 15px; display: flex; justify-content: space-between; align-items: center; font-size: 20px; font-weight: bold; color: #00a884; }
        .chat-area { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #0b141a; }
        .message { max-width: 75%; padding: 10px; border-radius: 8px; font-size: 14px; word-break: break-word; }
        .message.incoming { background: #202c33; align-self: flex-start; }
        .message.outgoing { background: #005c4b; align-self: flex-end; }
        .footer { padding: 10px 15px; background: #202c33; display: flex; gap: 10px; align-items: center; }
        .footer input { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 8px; color: #fff; outline: none; font-size: 14px; }
        .footer button { background: #00a884; border: none; padding: 10px 15px; border-radius: 8px; color: #fff; font-weight: bold; cursor: pointer; }
        #login-screen { position: fixed; inset: 0; background: #111b21; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; z-index: 100; }
        #login-screen input { width: 100%; max-width: 300px; padding: 12px; margin-bottom: 15px; background: #2a3942; border: none; border-radius: 8px; color: #fff; font-size: 16px; outline: none; }
        #login-screen button { width: 100%; max-width: 300px; padding: 12px; background: #00a884; border: none; border-radius: 8px; color: #fff; font-weight: bold; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>

    <div id="login-screen">
        <h2 style="color: #00a884; margin-bottom: 20px;">Bem-vindo ao PlugaDoz</h2>
        <input type="text" id="username-input" placeholder="Digite seu nome para entrar...">
        <button onclick="entrarChat()">Entrar no Chat</button>
    </div>

    <div class="app-container">
        <div class="header">
            <span>PlugaDoz</span>
            <span id="user-display" style="font-size: 14px; color: #8696a0;"></span>
        </div>
        <div class="chat-area" id="chat-messages">
            <div class="message incoming">Bem-vindo ao chat global do PlugaDoz! As mensagens trocadas aqui aparecem em tempo real para todos conectados.</div>
        </div>
        <div class="footer">
            <input type="text" id="message-input" placeholder="Digite uma mensagem..." onkeypress="checarEnter(event)">
            <button onclick="enviarMensagem()">Enviar</button>
        </div>
    </div>

    <script>
        const socket = io();
        let meuUsuario = "";

        function entrarChat() {
            const input = document.getElementById('username-input');
            const nome = input.value.trim();
            if(!nome) {
                alert("Por favor, digite seu nome!");
                return;
            }
            meuUsuario = nome;
            document.getElementById('user-display').innerText = "Conectado como: " + meuUsuario;
            document.getElementById('login-screen').style.display = 'none';
        }

        function enviarMensagem() {
            const input = document.getElementById('message-input');
            const texto = input.value.trim();
            if(!texto || !meuUsuario) return;

            socket.emit('nova_mensagem', { usuario: meuUsuario, texto: texto });
            input.value = '';
        }

        function checarEnter(e) {
            if(e.key === 'Enter') enviarMensagem();
        }

        socket.emit('usuario_entrou');

        socket.on('mensagem_recebida', function(dados) {
            const chat = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = dados.usuario === meuUsuario ? 'message outgoing' : 'message incoming';
            div.innerHTML = `<strong>${dados.usuario}:</strong> ${dados.texto}`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(APP_HTML)

@socketio.on('nova_mensagem')
def handle_message(data):
    # Envia a mensagem para todos os usuários conectados no mundo inteiro em tempo real
    socketio.emit('mensagem_recebida', data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
    
