import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key'

# Configuração do SocketIO em modo threading
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Histórico de mensagens na memória
mensagens_historico = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'itaboa-geral')
    join_room(room)
    emit('history', mensagens_historico)

@socketio.on('message')
def handle_message(data):
    room = data.get('room', 'itaboa-geral')
    mensagens_historico.append(data)
    emit('message', data, to=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    
