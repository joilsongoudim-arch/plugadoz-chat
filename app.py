import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_plugadoz'
socketio = SocketIO(app, cors_allowed_origins="*")

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        return "<script>alert('Usuário ou senha incorretos!'); window.location='/login';</script>"
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        if not username or not password:
            return "<script>alert('Preencha todos os campos!'); window.location='/register';</script>"
            
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return "<script>alert('Conta criada com sucesso! Faça login.'); window.location='/login';</script>"
        except sqlite3.IntegrityError:
            return "<script>alert('Esse nome de usuário já existe! Escolha outro.'); window.location='/register';</script>"
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)

@socketio.on('message')
def handle_message(data):
    socketio.emit('message', data, room=data['room'])

if __name__ == '__main__':
    socketio.run(app)
    
