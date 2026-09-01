from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-plugadoz'
socketio = SocketIO(app, cors_allowed_origins="*")

historico_mensagens = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    join_room(room)
    if room in historico_mensagens:
        emit('history', historico_mensagens[room])
    else:
        emit('history', [])

@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    leave_room(room)

@socketio.on('message')
def handle_message(data):
    room = data.get('room')
    if room:
        if room not in historico_mensagens:
            historico_mensagens[room] = []
        historico_mensagens[room].append(data)
        if len(historico_mensagens[room]) > 100:
            historico_mensagens[room].pop(0)
            
        emit('message', data, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
    
