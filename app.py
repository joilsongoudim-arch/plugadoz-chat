from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plugadoz Chat</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background-color: #121212; color: #e0e0e0; display: flex; flex-direction: column; height: 100vh; }
        header { background: #1f1f1f; padding: 15px; text-align: center; font-size: 1.2rem; font-weight: bold; border-bottom: 1px solid #333; }
        #chat-container { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .message { background: #2a2a2a; padding: 10px 15px; border-radius: 8px; max-width: 80%; word-break: break-word; }
        .message.mine { background: #005c4b; align-self: flex-end; }
        .input-area { display: flex; padding: 10px; background: #1f1f1f; border-top: 1px solid #333; }
        input { flex: 1; padding: 12px; border: none; border-radius: 4px; background: #2a2a2a; color: #fff; outline: none; font-size: 1rem; }
        button { background: #00a884; color: white; border: none; padding: 0 20px; margin-left: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <header>Plugadoz Chat</header>
    <div id="chat-container"></div>
    <div class="input-area">
        <input id="message-input" type="text" placeholder="Digite sua mensagem..." autocomplete="off">
        <button onclick="sendMessage()">Enviar</button>
    </div>

    <script>
        const socket = io();
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');

        function sendMessage() {
            const text = messageInput.value.trim();
            if (text) {
                socket.emit('send_message', { data: text });
                messageInput.value = '';
            }
        }

        messageInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        socket.on('receive_message', function(msg) {
            const div = document.createElement('div');
            div.className = 'message';
            div.textContent = msg.data;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('send_message')
def handle_message(message):
    emit('receive_message', {'data': message['data']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)
