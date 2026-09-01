import os
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-full-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# BANCO DE DADOS EM MEMÓRIA (tudo)
chats_db = {
    "Grupo Geral": []
}
status_db = []
grupos_lista = ["Grupo Geral"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_grupos')
def get_grupos():
    return jsonify(grupos_lista)

@app.route('/get_status')
def get_status():
    return jsonify(status_db)

@socketio.on('connect')
def on_connect():
    emit('grupos_atualizados', grupos_lista)
    emit('historico_status', status_db)
    emit('historico', chats_db.get("Grupo Geral", []))

@socketio.on('entrar_grupo')
def entrar_grupo(nome_grupo):
    if nome_grupo in chats_db:
        emit('historico', chats_db[nome_grupo])

@socketio.on('criar_grupo')
def criar_grupo(nome_grupo):
    nome_grupo = nome_grupo.strip()
    if nome_grupo and nome_grupo not in chats_db:
        chats_db[nome_grupo] = []
        grupos_lista.append(nome_grupo)
        emit('grupos_atualizados', grupos_lista, broadcast=True)

@socketio.on('mensagem')
def on_mensagem(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    grupo = data.get('grupo', 'Grupo Geral')
    if grupo not in chats_db:
        chats_db[grupo] = []
        grupos_lista.append(grupo)
    chats_db[grupo].append(data)
    if len(chats_db[grupo]) > 300:
        chats_db[grupo].pop(0)
    emit('nova_mensagem', {'grupo': grupo, 'mensagem': data}, broadcast=True)

@socketio.on('novo_status')
def on_novo_status(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    data['id'] = len(status_db) + 1
    status_db.insert(0, data)
    if len(status_db) > 100:
        status_db.pop()
    emit('status_novo', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
