import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from extensions import cfg, QUERY_TEXT
from logica import processar_dados_milling
from sqlalchemy import text
import pandas as pd
import datetime

# --- Configuração do Banco de Dados e Query ---
OracleSession = cfg.get_oracle_session()
SOCKET_URL = cfg.get_aplication_host()

app = Flask(__name__)
app.config["SECRET_KEY"] = cfg.get_aplication_key()
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Cache e Controle da Tarefa em Background ---

# Cache para armazenar o último resultado dos dados de moagem.
milling_data_cache = None
milling_data_update = None
# Usamos um Lock para garantir que a tarefa em background seja iniciada apenas uma vez.
background_task_lock = threading.Lock()
background_task_started = False

# --- Funções de Lógica ---

def fetch_and_process_data():
    """
    Busca os dados do Oracle, processa com a função `process_data`
    e retorna o payload pronto para ser enviado.
    """
    print("Buscando novos dados de moagem do Oracle...")
    try:
        with OracleSession() as session:
            stmt = text(QUERY_TEXT).execution_options()
            result = session.execute(stmt)
            
            # 1. Converte o resultado do cursor para DataFrame
            # result.keys() contém os nomes das colunas da QUERY_TEXT
            keys = [k.upper() for k in result.keys()]
            df_banco = pd.DataFrame(result.fetchall(), columns=keys)
            
            # 2. Executa a sanitização (Importante!)
            # Como os dados vêm do banco, os tipos podem vir corretos, 
            # mas garantir a sanitização evita quebras na lógica.
            # Reaproveite a lógica de conversão de tipos que criamos antes.
            
            # 3. Processa os dados
            processed_data = processar_dados_milling(df_banco)
            
            print("Dados buscados e processados com sucesso.")
            return processed_data
    except Exception as e:
        print(f"ERRO ao buscar dados do Oracle: {e}")
        return None # Retornar None em caso de erro para não limpar o cache com dados ruins

def background_milling_task():
    """
    Tarefa que roda em background para periodicamente buscar,
    cachear e emitir os dados de moagem.
    """
    global milling_data_cache, milling_data_update
    print("Iniciando a task de background para moagem.")
    while True:
        data = fetch_and_process_data()
        if data is not None:
            milling_data_cache = data
            milling_data_update = datetime.datetime.now().isoformat()
            print("Cache atualizado. Emitindo 'update_milling_data' para todos os clientes.")
            # Emite para todos os clientes conectados no namespace padrão
            socketio.emit('update_milling_data', milling_data_cache)
            socketio.emit('api_status', {'stats': 'online', 'last_update': milling_data_update})
            print('dados emitidos')

        # Espera 5 minutos (300 segundos) para a próxima execução.
        # Use socket_io.sleep() para não bloquear o servidor!
        socketio.sleep(300)


@app.route("/")
def index():
    return render_template("index.html", socket_url=SOCKET_URL)

# --- Handlers do Socket.IO ---

@socketio.on("connect")
def handle_connect():
    """
    Chamado quando um novo cliente se conecta.
    """
    global background_task_started
    print('Cliente conectado ao módulo com WebSocket')

    # Garante que a tarefa em background seja iniciada apenas uma vez.
    with background_task_lock:
        if not background_task_started:
            print("Iniciando a tarefa em background pela primeira vez.")
            socketio.start_background_task(target=background_milling_task)
            background_task_started = True

    # Se já temos dados em cache, envia para o cliente que acabou de conectar.
    if milling_data_cache:
        print("Enviando dados do cache para o novo cliente.")
        # O emit dentro de um handler de conexão envia apenas para o cliente atual.
        emit('update_milling_data', milling_data_cache)

@socketio.on("stats")
def send_status():
    socketio.emit('api_status', {'stats': 'online', 'last_update': milling_data_update})

@socketio.on("get_data")
def send_data():
    socketio.emit('api_data', milling_data_cache)

@socketio.on("mensagem")
def handle_msg(data):
    print(f'Mensagem recebida: {data}')

@socketio.on("disconnect")
def handle_disconnect():
    print("Cliente desconectado")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8020, debug=True, allow_unsafe_werkzeug=True)