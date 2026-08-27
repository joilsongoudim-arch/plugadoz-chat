from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_super_segura'
socketio = SocketIO(app)

usuarios_cadastrados = {}

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

@socketio.on('enviar_mensagem')
def handle_message(data):
    username = session.get('username', 'Anônimo')
    mensagem = data.get('mensagem')
    emit('receber_mensagem', {'username': username, 'mensagem': mensagem}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
    
