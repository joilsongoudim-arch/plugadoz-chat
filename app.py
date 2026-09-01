import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

chats_db = { "Grupo Geral": [] }
status_db = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chats/<nome_grupo>')
def get_chats(nome_grupo):
    return jsonify(chats_db.get(nome_grupo, []))

@app.route('/get_status')
def get_status():
    return jsonify(status_db)

@app.route('/post_status', methods=['POST'])
def post_status():
    data = request.get_json()
    data['hora'] = datetime.now().strftime('%H:%M')
    status_db.append(data)
    if len(status_db) > 50: status_db.pop(0)
    socketio.emit('novo_status', data, broadcast=True)
    return jsonify({"status": "ok"})

@socketio.on('mensagem')
def handle_mensagem(data):
    # data pode ter 'texto' ou 'audio' (base64)
    data['hora'] = datetime.now().strftime('%H:%M')
    grupo = data.get('grupo', 'Grupo Geral')
    if grupo not in chats_db: chats_db[grupo] = []
    chats_db[grupo].append(data)
    if len(chats_db[grupo]) > 100: chats_db[grupo].pop(0)
    emit('nova_mensagem', {'grupo': grupo, 'mensagem': data}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
