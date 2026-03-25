# MillingStream - Roadmap de Evolução 🚀

Este documento lista as tarefas pendentes e sugestões de melhoria para levar o projeto ao nível de produção.

## 🟢 Fase 1: Fundação e Robustez (Curto Prazo)
- [ ] **Implementar Logging Profissional:** Substituir `print()` pelo módulo `logging` do Python, configurando níveis (INFO, ERROR, DEBUG) e salvamento em arquivo.
- [ ] **Refinar .env e Configurações:** Centralizar todas as configurações (como tempo de atualização e limites de meta) no `extensions.py` lendo do `.env`.
- [ ] **Tratamento de Exceções Global:** Criar um decorador ou handler para capturar erros inesperados no Socket.IO e notificar o usuário de forma amigável.
- [ ] **Refatorar Query SQL:** Mover a `QUERY_TEXT` para um arquivo `.sql` separado ou uma constante mais organizada, facilitando a manutenção.

## 🟡 Fase 2: Otimização do Socket.IO (Padrões de Mercado)
- [ ] **Inicialização da Task:** Mover a lógica de início da `background_milling_task` para fora do `handle_connect`, utilizando um hook de inicialização do Flask ou um scheduler.
- [ ] **Uso de Namespaces:** Migrar os eventos de moagem para um namespace dedicado (ex: `/moagem`).
- [ ] **Evento de Erro Dedicado:** Criar um evento `api_error` para informar o front-end quando a conexão com o Oracle falhar.
- [ ] **Health Check:** Implementar um evento de "heartbeat" mais robusto para monitorar a saúde da conexão entre o servidor e o banco de dados.

## 🟠 Fase 3: Performance e Dados (Médio Prazo)
- [ ] **Otimização Pandas:** Revisar o método `calcular_metricas_agrupadas` para garantir que não haja vazamento de memória com dataframes muito grandes.
- [ ] **Tipagem Estática:** Adicionar Type Hints em todas as funções para melhorar a legibilidade e evitar bugs de tipo.
- [ ] **Validação de Schema:** Utilizar Pydantic ou Marshmallow para validar os dados vindos do banco antes do processamento.
- [ ] **Caching Externo (Opcional):** Avaliar o uso de Redis para armazenar o cache de moagem, permitindo escalar a aplicação para múltiplos workers.

## 🔵 Fase 4: Frontend e UX (Polimento)
- [ ] **Feedback Visual de Loading:** Mostrar um estado de "carregando" ou "atualizando" no `index.html` enquanto os dados estão sendo buscados.
- [ ] **Tratamento de Reconexão:** Garantir que o front-end saiba lidar com quedas de conexão do WebSocket, tentando reconectar automaticamente.
- [ ] **Dark Mode / UI Polish:** Refinar o CSS do `templates/index.html` para um visual mais industrial e moderno.

## ⚪ Fase 5: CI/CD e Qualidade
- [ ] **Testes Unitários:** Criar testes para a lógica de cálculo de ATR e Impureza em `logica.py`.
- [ ] **Dockerfile:** Criar um arquivo Docker para facilitar o deploy e garantir que o ambiente (com Oracle Client) seja reprodutível.
- [ ] **Documentação da API:** Documentar os eventos de Socket.IO (entrada e saída) no README.md.
