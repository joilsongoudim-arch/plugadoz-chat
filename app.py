import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-clone'
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=20*1024*1024)

mensagens = []
status = []
perfis = {}
grupos = [{"id":"geral","nome":"grupo de família","foto":"https://i.pravatar.cc/100?img=12"}]

@app.route('/')
def index(): return render_template('index.html')

@socketio.on('connect')
def c():
    emit('historico', mensagens)
    emit('status_historico', status)
    emit('grupos_historico', grupos)
    emit('perfis_historico', perfis)

@socketio.on('mensagem')
def m(d):
    d['id'] = str(len(mensagens))+datetime.now().strftime('%M%S')
    d['hora'] = datetime.now().strftime('%H:%M')
    mensagens.append(d)
    emit('nova_mensagem', d, broadcast=True)

@socketio.on('apagar_msg')
def apagar(data):
    global mensagens
    mensagens = [x for x in mensagens if x.get('id')!=data['id']]
    emit('msg_apagada', data, broadcast=True)

@socketio.on('postar_status')
def ps(d):
    d['hora']=datetime.now().strftime('%H:%M')
    d['id']=len(status)+1
    status.insert(0,d)
    emit('novo_status', d, broadcast=True)

@socketio.on('salvar_perfil')
def sp(d):
    perfis[d['nome']]=d
    emit('perfil_atualizado', d, broadcast=True)

@socketio.on('criar_grupo')
def cg(d):
    grupos.append(d)
    emit('grupo_criado', d, broadcast=True)

if __name__ == '__main__':
    port=int(os.environ.get('PORT',10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
