from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# guarda mensagens na memória (depois você troca por banco de dados)
mensagens = []
usuarios_online = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Usuário conectou')
    emit('historico', mensagens)

@socketio.on('mensagem')
def handle_mensagem(data):
    # data = {'usuario': 'Joilson', 'texto': 'e aí', 'hora': '...'}
    mensagens.append(data)
    # manda pra TODO MUNDO em tempo real igual WhatsApp
    emit('nova_mensagem', data, broadcast=True)

@socketio.on('digitando')
def handle_digitando(data):
    emit('digitando', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
