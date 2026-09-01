from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Banco em memória estruturado por salas/grupos
# Ex: {"Grupo Geral": [mensagens...], "Meu Novo Grupo": [mensagens...]}
chats_db = {
    "Grupo Geral": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chats', methods=['GET'])
def listar_chats():
    return jsonify(list(chats_db.keys()))

@app.route('/api/chats', methods=['POST'])
def criar_chat():
    data = request.json
    nome_grupo = data.get('nome')
    if nome_grupo and nome_grupo not in chats_db:
        chats_db[nome_grupo] = []
        return jsonify({"status": "success", "grupo": nome_grupo})
    return jsonify({"status": "error", "message": "Grupo já existe ou nome inválido"})

@app.route('/api/chat/<path:nome_grupo>', methods=['GET', 'POST'])
def handle_chat_especifico(nome_grupo):
    if nome_grupo not in chats_db:
        chats_db[nome_grupo] = []

    if request.method == 'POST':
        data = request.json
        if data:
            chats_db[nome_grupo].append(data)
            if len(chats_db[nome_grupo]) > 100:
                chats_db[nome_grupo].pop(0)
        return jsonify({"status": "success"})
    
    return jsonify(chats_db[nome_grupo])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
