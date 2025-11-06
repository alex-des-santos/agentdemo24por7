# Agente 24/7 para Tickets – Orquestrador e Multi-Agentes

Caso de trabalho: um agente operando 24/7 para tratar tickets automaticamente, com orquestração e uso de múltiplos “agentes” especializados quando necessário.

Este projeto demonstra um fluxo de automação com orquestrador (pode ser LangGraph, LangChain, Agno ou similar). Aqui usamos um grafo de estados para deixar o fluxo claro e controlável.

## Objetivo

Funcionário que trabalha 24/7: precisamos de um agente (com orquestrador) que:

- Verifica os tickets no Ticket Manager.
- Verifica se há algum ticket que o agente sabe/pode resolver.
- Se sim: recebe o Ticket ID, coleta as informações disponíveis do ticket, investiga e tenta resolver. Em seguida, executa o comando/ação de resolução.
  - Desbloquear o usuário e resetar a senha; verificar novamente o desbloqueio do usuário.
  - Enviar um e-mail para o gestor avisando que foi preciso resetar a senha; caso não haja gestor, enviar e-mail ao próprio usuário.
- Se não: adiciona uma observação do que foi feito/analisado e escala para a equipe apropriada.

## Como funciona (visão geral)

1) Integração com Ticket Manager
- Lê a fila de tickets (dados locais em `data/tickets.json`).
- Lista os tickets abertos e prepara para processamento.

2) Classificação e decisão
- Classifica o tipo do ticket usando um serviço externo de classificação.
- Decide se o caso é automatizável (playbook disponível) ou se precisa ser escalado.

3) Execução do playbook
- Busca dados do usuário no serviço de identidade simulado.
- Executa ações como desbloqueio e reset de senha.
- Verifica o resultado (ex.: usuário está desbloqueado?).

4) Notificação e atualização
- Registra comentários no ticket com o que foi feito.
- Atualiza status (Resolvido ou Escalado).
- Envia e-mails de notificação ao usuário e/ou gestor, conforme o caso.

## Componentes

```
agentdemo/
├── tools/                      # Serviços simulados
│   ├── ticket_manager.py      # Gerenciamento de tickets (JSON local)
│   ├── identity_service.py    # Identidade/AD (simulado)
│   └── email_service.py       # Envio de e-mail (simulado)
├── data/
│   └── tickets.json           # Base de tickets de exemplo
├── graph.py                    # Grafo de estados (orquestração do fluxo)
├── classifier.py               # Classificação dos tickets (serviço externo)
├── app.py                      # Interface web (Streamlit)
├── main.py                     # Execução via linha de comando
└── README.md
```

## Executando

- Interface Web (Streamlit):
```bash
streamlit run app.py
```
- Linha de comando (CLI):
```bash
python main.py
```

Observação: para a classificação, defina a credencial do serviço (por exemplo, `OPENAI_API_KEY` ou `MODEL_API_KEY`).

## Fluxo resumido

- Coletar tickets → Classificar → Decidir (automatizar ou escalar) → Executar playbook → Notificar → Atualizar status.

## Escopo de resolução (exemplos)

- Desbloqueio de conta (Email, Azure/AD, Windows).
- Reset de senha e confirmação do desbloqueio.
- Notificações ao gestor e/ou usuário.

Quando não é automatizável, o agente deixa observações claras e escala.

## Notas

- Os serviços (identidade, e-mail) são simulados para fins de demonstração.
- O grafo de estados facilita entender o que foi feito e por quê, sem truques.
- Pode conter pequenos erros gramaticais propositalmente, isso não muda a funcionalidade.
