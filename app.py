import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

chats = []
status = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def connect():
    emit('historico', chats)
    emit('historico_status', status)

@socketio.on('mensagem')
def msg(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    chats.append(data)
    if len(chats) > 200: chats.pop(0)
    emit('nova_mensagem', data, broadcast=True)

@socketio.on('novo_status')
def st(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    status.insert(0, data)
    emit('status_novo', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
