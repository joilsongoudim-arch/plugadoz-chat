import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plugadoz-secret-key'

# Histórico armazenado na memória do servidor
mensagens_historico = []
status_historico = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mensagens', methods=['GET', 'POST'])
def gerenciar_mensagens():
    if request.method == 'POST':
        dados = request.json
        if dados and dados.get('text'):
            mensagens_historico.append(dados)
            return jsonify({'status': 'sucesso', 'mensagem': dados})
        return jsonify({'status': 'erro'}), 400
    return jsonify(mensagens_historico)

@app.route('/api/status', methods=['GET', 'POST'])
def gerenciar_status():
    if request.method == 'POST':
        dados = request.json
        if dados:
            status_historico.append(dados)
            return jsonify({'status': 'sucesso'})
        return jsonify({'status': 'erro'}), 400
    return jsonify(status_historico)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    
