import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-hard'
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10*1024*1024)

mensagens = []
status_list = []
perfis = {}  # nome -> {foto, recado}
grupos = [{"id":"geral","nome":"Grupo Plugadoz","foto":"https://i.pravatar.cc/100?img=65","membros":[]}]

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def conn():
    emit('historico', mensagens)
    emit('status_historico', status_list)
    emit('grupos_historico', grupos)
    emit('perfis_historico', perfis)

@socketio.on('mensagem')
def msg(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    mensagens.append(data)
    if len(mensagens) > 500:
        mensagens.pop(0)
    emit('nova_mensagem', data, broadcast=True)

@socketio.on('postar_status')
def st(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    data['id'] = len(status_list)+1
    status_list.insert(0, data)
    emit('novo_status', data, broadcast=True)

@socketio.on('salvar_perfil')
def perfil(data):
    perfis[data['nome']] = {"foto":data.get('foto',""),"recado":data.get('recado',"Disponível"),"nome":data['nome']}
    emit('perfil_atualizado', perfis[data['nome']], broadcast=True)

@socketio.on('criar_grupo')
def criar_grupo(data):
    data['id'] = data['nome'].lower().replace(" ","_")
    grupos.append(data)
    emit('grupo_criado', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
