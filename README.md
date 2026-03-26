# MillingStream

Sistema de monitoramento e processamento de dados de moagem em tempo real, utilizando Flask e WebSockets.

O **MillingStream** integra-se a um banco de dados Oracle para extrair dados de cargas (moagem), processa métricas críticas como **ATR** (Açúcar Total Recuperável) e **Impureza Mineral**, e transmite essas atualizações para os clientes conectados via Socket.IO.

## 🚀 Funcionalidades

- **Atualização em Tempo Real:** Utiliza WebSockets (Flask-SocketIO) para enviar dados processados aos dashboards sem necessidade de recarregar a página.
- **Processamento de Dados com Pandas:** Cálculos complexos de séries temporais, acumulação de moagem e fórmulas de qualidade (ATR) realizados de forma eficiente.
- **Cache Inteligente:** Mantém o último estado dos dados em memória para entrega imediata a novos clientes.
- **Tarefa em Background:** Busca automática de novos dados no banco Oracle a cada 5 minutos.
- **Integração Oracle:** Configuração robusta com SQLAlchemy e `oracledb`, incluindo suporte a Oracle Instant Client e TNS.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.x, Flask
- **Comunicação:** Flask-SocketIO (WebSockets)
- **Banco de Dados:** Oracle (via SQLAlchemy & oracledb)
- **Análise de Dados:** Pandas, NumPy
- **Frontend:** HTML5, Jinja2 (Templates Flask)

## 📋 Pré-requisitos

1. **Oracle Instant Client:** É necessário ter o Oracle Instant Client instalado e configurado na máquina para a conexão com o banco.
2. **Dependências Python:**
   ```bash
   pip install flask flask-socketio sqlalchemy pandas numpy oracledb python-dotenv
   ```

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Banco de Dados Oracle
INSTANT_CLIENT=C:\caminho\para\instantclient
TSN=NOME_DO_SEU_TNS
DB_USER=seu_usuario
DB_PASS=sua_senha

# Aplicação
SECRET=sua_chave_secreta_aqui
```

### Como gerar a chave:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

copiar o resultado e colocar no .env

## 🏃 Como Executar

1. Certifique-se de que o Oracle Instant Client está no caminho especificado no `.env`.
2. Execute a aplicação:
   ```bash
   python app.py
   ```
3. Acesse no navegador: `http://localhost:5000`

## 📊 Estrutura do Projeto

- `app.py`: Servidor Flask, rotas e lógica do WebSocket.
- `logica.py`: Núcleo de processamento de dados (Pandas/Numpy) e fórmulas de moagem.
- `extensions.py`: Configuração de conexão com o banco de dados e queries SQL.
- `templates/`: Arquivos HTML da interface.

---
Desenvolvido para monitoramento industrial de alta performance.
