import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Histórico de mensagens guardado por sala para não sumir ao trocar de chat
historico_mensagens = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    join_room(room)
    # Envia o histórico da sala específica para quem acabou de entrar
    if room in historico_mensagens:
        emit('history', historico_mensagens[room])
    else:
        emit('history', [])

@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    leave_room(room)

@socketio.on('message')
def handle_message(data):
    room = data.get('room')
    if not room:
        return
    
    if room not in historico_mensagens:
        historico_mensagens[room] = []
    
    # Salva a mensagem no histórico da sala
    historico_mensagens[room].append(data)
    
    # Envia a mensagem em tempo real para todo mundo na mesma sala
    emit('message', data, room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
