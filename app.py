from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# HTML com a interface completa igual ao WhatsApp
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Web</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: #0b141a; height: 100vh; display: flex; flex-direction: column; color: #e9edef; }
        
        /* Cabeçalho */
        header { background-color: #202c33; padding: 10px 16px; display: flex; align-items: center; height: 60px; border-bottom: 1px solid #222d34; }
        .avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #00a884; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff; margin-right: 12px; }
        .contact-info h2 { font-size: 16px; font-weight: 500; }
        .contact-info p { font-size: 12px; color: #8696a0; }

        /* Área de Mensagens */
        #chat-container { flex: 1; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d04fcded21.png'); background-repeat: repeat; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        
        .message { max-width: 65%; padding: 8px 12px; border-radius: 7.5px; font-size: 14px; line-height: 19px; position: relative; word-wrap: break-word; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }
        .message.incoming { background-color: #202c33; align-self: flex-start; border-top-left-radius: 0; }
        .message.outgoing { background-color: #005c4b; align-self: flex-end; border-top-right-radius: 0; }
        .time { font-size: 11px; color: #8696a0; float: right; margin-left: 8px; margin-top: 4px; line-height: 15px; }

        /* Rodapé / Input */
        footer { background-color: #202c33; padding: 10px 16px; display: flex; align-items: center; gap: 10px; height: 60px; }
        input { flex: 1; background-color: #2a3942; border: none; border-radius: 8px; padding: 12px 16px; color: #e9edef; font-size: 15px; outline: none; }
        input::placeholder { color: #8696a0; }
        button { background-color: #00a884; border: none; border-radius: 50%; width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.2s; }
        button svg { fill: #fff; width: 20px; height: 20px; }
        button:hover { background-color: #01755c; }
    </style>
</head>
<body>

    <header>
        <div class="avatar">AI</div>
        <div class="contact-info">
            <h2>Assistente Plugadoz</h2>
            <p>online</p>
        </div>
    </header>

    <div id="chat-container">
        <div class="message incoming">
            Olá! Interface do WhatsApp carregada com sucesso na nuvem. Como posso te ajudar hoje?
            <span class="time">06:38</span>
        </div>
    </div>

    <footer>
        <input type="text" id="message-input" placeholder="Digite um texto..." autofocus>
        <button onclick="sendMessage()">
            <svg viewBox="0 0 24 24"><path d="M1.101 21.75 23.8 12.028 1.101 2.3l.011 7.912 13.623 1.816-13.623 1.817-.011 7.912z"></path></svg>
        </button>
    </footer>

    <script>
        const input = document.getElementById('message-input');
        const container = document.getElementById('chat-container');

        input.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                sendMessage();
            }
        });

        function sendMessage() {
            const text = input.value.trim();
            if (!text) return;

            const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            // Adiciona mensagem enviada
            container.innerHTML += `
                <div class="message outgoing">
                    ${text}
                    <span class="time">${now}</span>
                </div>
            `;
            input.value = '';
            container.scrollTop = container.scrollHeight;

            // Simula resposta automática do bot
            setTimeout(() => {
                container.innerHTML += `
                    <div class="message incoming">
                        Recebi sua mensagem: "${text}"! Tudo funcionando redondinho no Render. 🚀
                        <span class="time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                `;
                container.scrollTop = container.scrollHeight;
            }, 1000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
