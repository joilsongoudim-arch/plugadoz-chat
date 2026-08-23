import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-simples'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Direto</title>
    <style>
        body { background: #111b21; color: #fff; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        #login { position: fixed; inset: 0; background: #111b21; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; z-index: 10; }
        #login input, #login button { width: 80%; max-width: 300px; padding: 12px; margin: 8px; border-radius: 20px; border: none; font-size: 16px; }
        #login button { background: #00a884; color: white; font-weight: bold; cursor: pointer; }
        #chat { display: flex; flex-direction: column; height: 100%; }
        #mensagens { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 8px; }
        .msg { background: #202c33; padding: 10px; border-radius: 8px; max-width: 75%; word-break: break-word; }
        .msg.eu { background: #005c4b; align-self: flex-end; }
        .footer { background: #202c33; padding: 10px; display: flex; gap: 8px; }
        .footer input { flex: 1; padding: 10px; border-radius: 20px; border: none; outline: none; background: #2a3942; color: #fff; font-size: 15px; }
        .footer button { background: #00a884; border: none; color: white; padding: 0 20px; border-radius: 20px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

    <div id="login">
        <h2>Entrar no Chat</h2>
        <input type="text" id="nomeUser" placeholder="Seu apelido">
        <button onclick="entrarChat()">Entrar</button>
    </div>

    <div id="chat" style="display:none;">
        <div id="mensagens"></div>
        <div class="footer">
            <input type="text" id="textoMsg" placeholder="Digite uma mensagem..." onkeypress="if(event.key==='Enter')enviar()">
            <button onclick="enviar()">Enviar</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        let meuNome = '';

        function entrarChat() {
            let val = document.getElementById('nomeUser').value.trim();
            if(!val) { alert('Digite um nome!'); return; }
            meuNome = val;
            document.getElementById('login').style.display = 'none';
            document.getElementById('chat').style.display = 'flex';
        }

        function enviar() {
            let input = document.getElementById('textoMsg');
            let txt = input.value.trim();
            if(!txt) return;
            socket.emit('mensagem_cliente', { nome: meuNome, texto: txt });
            input.value = '';
        }

        socket.on('mensagem_servidor', function(data) {
            let box = document.getElementById('mensagens');
            let ehEu = data.nome === meuNome;
            box.innerHTML += `<div class="msg ${ehEu ? 'eu' : ''}"><strong>${data.nome}:</strong> ${data.texto}</div>`;
            box.scrollTop = box.scrollHeight;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('mensagem_cliente')
def handle_msg(data):
    socketio.emit('mensagem_servidor', data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    
