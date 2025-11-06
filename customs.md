# customs.md

Este arquivo lista o que pode ser customizado com segurança sem quebrar o código. Para mudanças além do descrito, faça com cuidado e teste.

- Caminho: `README.md`
  - Nome: README.md
  - Pode editar: todo o conteúdo do documento (texto, exemplos, seções).

- Caminho: `.gitignore`
  - Nome: .gitignore
  - Pode editar: incluir/remover padrões de arquivos/diretórios a ignorar.

- Caminho: `.env.example`
  - Nome: .env.example
  - Pode editar: valores de exemplo. Mantenha a chave `MODEL_API_KEY` (e variáveis adicionais, se desejar).

- Caminho: `.streamlit/config.toml`
  - Nome: config.toml
  - Pode editar: `address`, `port`, `headless` conforme necessário.

- Caminho: `data/tickets.json`
  - Nome: tickets.json
  - Pode editar: lista de tickets e seus campos de exemplo.
  - Observações: mantenha os campos `id`, `requester`, `title`, `description`, `status` (com valor `open` para ser processado).

- Caminho: `app.py`
  - Nome: app.py
  - Pode editar: textos da interface (títulos, descrições, mensagens da sidebar), rótulos de botões, ícones, e valores padrão de controles.
  - Não alterar: nomes de funções públicas (`main`, etc.), imports, chamadas a `build_graph()` e a checagem de credenciais.

- Caminho: `graph.py`
  - Nome: graph.py
  - Pode editar: mensagens de log/print, textos de comentários adicionados aos tickets, rótulos de status de saída (mantendo semântica).
  - Não alterar: nomes de nós/funções (`node_*`), roteamento e chaves do estado sem entender impacto.

- Caminho: `classifier.py`
  - Nome: classifier.py
  - Pode editar: lista de categorias e palavras-chave; regras de classificação e extração de sistema.
  - Não alterar: assinaturas e nomes de funções públicas (`classify_ticket_intent`, `analyze_automation_capability`, `extract_system_from_description`, `generate_resolution_summary`).

- Caminho: `tools/email_service.py`
  - Nome: email_service.py
  - Pode editar: templates de assunto/corpo dos e-mails e mensagens de log.
  - Não alterar: nomes de funções exportadas usadas por outros módulos.

- Caminho: `tools/identity_service.py`
  - Nome: identity_service.py
  - Pode editar: parâmetros como tamanho da senha temporária, conjunto de caracteres, mensagens de log.
  - Não alterar: nomes de funções e estrutura de retorno esperada (`ok`, `temp_password`, etc.).

- Caminho: `tools/ticket_manager.py`
  - Nome: ticket_manager.py
  - Pode editar: mensagens de log e formatação textual.
  - Não alterar: caminho base de dados (`DATA_PATH`) e chaves de retorno das funções.

- Caminho: `pyproject.toml`
  - Nome: pyproject.toml
  - Pode editar: metadados do projeto e adicionar dependências.
  - Cuidado: remover dependências existentes pode quebrar a execução.

- Caminho: `uv.lock`
  - Nome: uv.lock
  - Não recomendado editar manualmente (arquivo de lock de dependências).
