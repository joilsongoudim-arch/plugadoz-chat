from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_super_segura'
socketio = SocketIO(app)

# Dicionário temporário para guardar os usuários cadastrados { "usuario": "senha" }
usuarios_cadastrados = {}

# Lista de usuários atualmente online no chat
usuarios_online = {}

@app.route('/', methods=['GET'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in usuarios_cadastrados and usuarios_cadastrados[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Usuário ou senha incorretos! <a href='/login'>Tentar novamente</a>"
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in usuarios_cadastrados:
            return "Este usuário já existe! <a href='/register'>Tentar outro</a>"
        
        usuarios_cadastrados[username] = password
        session['username'] = username
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('connect')
def handle_connect():
    # Se o usuário estiver na sessão, adiciona à lista de online
    if 'username' in session:
        username = session['username']
        usuarios_online[request.sid] = username
        # Envia a lista atualizada para todo mundo no chat
        emit('atualizar_usuarios', list(usuarios_online.values()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in usuarios_online:
        usuarios_online.pop(request.sid)
        # Atualiza a lista para todo mundo quando alguém sai
        emit('atualizar_usuarios', list(usuarios_online.values()), broadcast=True)

@socketio.on('enviar_mensagem')
def handle_message(data):
    username = session.get('username', 'Anônimo')
    mensagem = data.get('mensagem')
    emit('receber_mensagem', {'username': username, 'mensagem': mensagem}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
    
