from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Histórico simples (depois a gente troca por banco de dados)
mensagens = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('historico', mensagens)

@socketio.on('mensagem')
def handle_mensagem(data):
    data['hora'] = datetime.now().strftime('%H:%M')
    mensagens.append(data)
    # manda pra todo mundo igual WhatsApp
    emit('nova_mensagem', data, broadcast=True)
    # mantém só as últimas 200 pra não pesar
    if len(mensagens) > 200:
        mensagens.pop(0)

@socketio.on('digitando')
def handle_digitando(data):
    emit('digitando', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app)
