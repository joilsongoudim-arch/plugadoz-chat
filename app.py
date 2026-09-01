from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'segredo!'
socketio = SocketIO(app, cors_allowed_origins="*")

historico_mensagens = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'geral')
    join_room(room)
    if room in historico_mensagens:
        emit('history', historico_mensagens[room])
    else:
        emit('history', [])

@socketio.on('message')
def handle_message(data):
    room = data.get('room', 'geral')
    if room not in historico_mensagens:
        historico_mensagens[room] = []
    historico_mensagens[room].append(data)
    socketio.emit('message', data, room=room)

if __name__ == '__main__':
    socketio.run(app)
    
