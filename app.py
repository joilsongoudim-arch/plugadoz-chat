import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Seu banco em memória por grupos - sua ideia tava certa
chats_db = {
    "Grupo Geral": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chats/<nome_grupo>')
def get_chats(nome_grupo):
    return jsonify(chats_db.get(nome_grupo, []))

@app.route('/send/<nome_grupo>', methods=['POST'])
def send_chat(nome_grupo):
    data = request.get_json()
    data['hora'] = datetime.now().strftime('%H:%M')
    
    if nome_grupo not in chats_db:
        chats_db[nome_grupo] = []
    
    chats_db[nome_grupo].append(data)
    
    if len(chats_db[nome_grupo]) > 100:
        chats_db[nome_grupo].pop(0)
    
    # manda em tempo real pra quem tiver na sala
    socketio.emit('nova_mensagem', {'grupo': nome_grupo, 'mensagem': data}, broadcast=True)
    
    return jsonify({"status": "success"})

@socketio.on('entrar_grupo')
def handle_entrar_grupo(nome_grupo):
    if nome_grupo in chats_db:
        emit('historico', chats_db[nome_grupo])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
