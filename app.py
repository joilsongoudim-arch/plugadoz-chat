from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-local')

lock = threading.Lock()
chats_db = {
    "Grupo Geral": []
}
status_historico = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mensagens', methods=['GET','POST'])
def gerenciar_mensagens():
    sala = request.args.get('sala', 'Grupo Geral')

    if request.method == 'POST':
        dados = request.json
        if not dados:
            return jsonify({"error": "dados inválidos"}), 400
            
        msg = {
            "sender": dados.get('sender'),
            "text": dados.get('text'),
            "time": dados.get('time')
        }
        with lock:
            if sala not in chats_db:
                chats_db[sala] = []
            chats_db[sala].append(msg)
            if len(chats_db[sala]) > 200:
                chats_db[sala].pop(0)
        return jsonify({"ok": True})

    with lock:
        return jsonify(chats_db.get(sala, []))

@app.route('/api/status', methods=['GET','POST'])
def status():
    if request.method == 'POST':
        dados = request.json
        if not dados:
            return jsonify({"error": "dados inválidos"}), 400
        with lock:
            status_historico.append(dados)
            if len(status_historico) > 50:
                status_historico.pop(0)
        return jsonify({"ok": True})
    with lock:
        return jsonify(status_historico)

@app.route('/health')
def health():
    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
