import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key'

# Configuração do SocketIO sem exigir workers assíncronos pesados
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Histórico simples em memória para não quebrar
mensagens_historico = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'itaboa-geral')
    join_room(room)
    # Envia o histórico assim que o usuário entra
    emit('history', mensagens_historico)

@socketio.on('message')
def handle_message(data):
    room = data.get('room', 'itaboa-geral')
    mensagens_historico.append(data)
    # Transmite a mensagem para todos na sala
    emit('message', data, to=room)

if __name__ == '__main__':
    # Captura a porta exata que o Render fornece no ambiente
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
    
