"""Interface Streamlit para o fluxo automatizado de tickets."""

from typing import Any, Dict, List
import os
import sys
import traceback

import streamlit as st

try:
    from graph import build_graph
    from tools import ticket_manager
except Exception as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.code(traceback.format_exc())
    st.stop()

Ticket = Dict[str, Any]


def configure_page() -> None:
    """Define metadados da pagina e o conteudo do cabecalho no Streamlit."""
    st.set_page_config(
        page_title="Sistema de Gerenciamento Automatico de Tickets",
        page_icon=":ticket:",
        layout="wide",
    )
    st.title(":ticket: Sistema de Gerenciamento Automatico de Tickets")
    st.markdown("### Orquestracao de Agentes com LangGraph")


def require_api_key() -> None:
    """Verifica se há credencial configurada para o serviço de classificação (quando aplicável)."""
    # Tentar obter a chave de várias fontes
    api_key = None
    
    # 1. Variáveis de ambiente
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MODEL_API_KEY")
    
    # 2. Streamlit secrets
    if not api_key and hasattr(st, 'secrets'):
        try:
            api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("MODEL_API_KEY")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        except Exception:
            pass
    
    if not api_key:
        st.warning("Chave do serviço de classificaçao nao configurada. Algumas funcoes podem nao operar.")


def load_open_tickets() -> List[Ticket]:
    """Busca todos os tickets em aberto e encerra a execucao se a fila estiver vazia."""
    tickets = ticket_manager.get_open_tickets()
    if not tickets:
        st.warning("Nenhum ticket aberto encontrado na fila.")
        st.stop()
    return tickets


def render_sidebar_summary(tickets: List[Ticket]) -> bool:
    """Renderiza os controles da barra lateral e informacoes contextuais."""
    st.sidebar.header("Configuracoes")
    auto_process = st.sidebar.checkbox("Processar automaticamente ao carregar", value=False)
    st.sidebar.success(f"{len(tickets)} tickets abertos na fila")

    results = st.session_state.get("results") or []
    escalated = sum(1 for item in results if "Escalado" in item.get("status", ""))
    if escalated:
        st.sidebar.warning(f"{escalated} tickets escalados")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sobre")
    st.sidebar.info(
        """Este sistema utiliza:
- Bibliotecas Python para orquestracao de fluxo
- Servicos internos para classificacao e regras
- Streamlit para interface
"""
    )
    st.sidebar.markdown("### Fluxo de Trabalho")
    st.sidebar.markdown(
        """1. Classificacao de intencao
2. Identificacao do sistema
3. Analise de automacao
4. Execucao de playbook
5. Notificacao e atualizacao
"""
    )
    return auto_process


def render_ticket_list_tab(tickets: List[Ticket]) -> None:
    """Exibe os tickets que estao na fila para automacao."""
    st.header("Tickets pendentes")

    for ticket in tickets:
        header = f"Ticket #{ticket['id']} - {ticket['title']}"
        with st.expander(header, expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Solicitante:** {ticket['requester_name']}")
                st.write(f"**Email:** {ticket['requester']}")
                st.write(f"**Status atual:** {ticket['status']}")

            with col2:
                st.write(f"**Gestor:** {ticket.get('manager', 'N/A')}")
                st.write(f"**Data de abertura:** {ticket['created_at']}")

            st.write("**Descricao do problema:**")
            st.info(ticket["description"])


def process_all_tickets(tickets: List[Ticket]) -> List[Dict[str, Any]]:
    """Executa o fluxo do LangGraph para cada ticket e apresenta o progresso."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    app = build_graph()
    results: List[Dict[str, Any]] = []

    for idx, ticket in enumerate(tickets, start=1):
        status_text.text(f"Processando Ticket #{ticket['id']} ({idx}/{len(tickets)})...")

        with st.expander(f"Log do Ticket #{ticket['id']} - {ticket['title']}", expanded=True):
            try:
                result = app.invoke({"ticket": ticket})

                ticket_result = {
                    "ticket_id": ticket["id"],
                    "title": ticket["title"],
                    "status": result.get("final_status", "Desconhecido"),
                    "intent": result.get("intent", "N/A"),
                    "system": result.get("system", "N/A"),
                    "resolution": result.get("resolution_summary", ""),
                    "error": result.get("error_message", ""),
                }
                results.append(ticket_result)

                if ticket_result["status"] == "Resolvido":
                    st.success(f"Ticket #{ticket['id']} resolvido com sucesso!")
                else:
                    st.warning(f"Ticket #{ticket['id']} escalado para analise manual.")

                st.json(result)
            except Exception as exc:
                st.error(f"Erro ao processar ticket #{ticket['id']}: {exc}")
                failure = {
                    "ticket_id": ticket["id"],
                    "title": ticket["title"],
                    "status": "Erro",
                    "intent": "N/A",
                    "system": "N/A",
                    "resolution": "",
                    "error": str(exc),
                }
                results.append(failure)

        progress_bar.progress(idx / len(tickets))

    status_text.text("Processamento concluido!")
    st.balloons()
    return results


def process_tickets_tab(tickets: List[Ticket], auto_process: bool) -> None:
    """Disponibiliza controles para executar a automacao em todos os tickets."""
    st.header("Processamento automatico")
    st.markdown(
        """O sistema processa **todos os tickets pendentes** automaticamente:
1. Classificar a intencao do ticket
2. Identificar o sistema afetado
3. Avaliar se o caso pode ser automatizado
4. Executar o playbook de resolucao (quando aplicavel)
5. Notificar usuario e gestor
6. Escalar quando nao for possivel resolver
"""
    )

    st.info(f"**{len(tickets)} tickets** na fila aguardando processamento")

    if not auto_process:
        st.session_state.pop("auto_processed", None)

    trigger_manual = st.button(
        "Processar TODOS os tickets pendentes",
        type="primary",
        use_container_width=True,
    )
    should_run = trigger_manual

    if auto_process and not st.session_state.get("auto_processed"):
        should_run = True
        st.session_state["auto_processed"] = True

    if should_run:
        st.session_state["results"] = process_all_tickets(tickets)


def render_results_tab() -> None:
    """Resume os resultados da execucao de automacao mais recente."""
    st.header("Resultados do processamento")

    results = st.session_state.get("results") or []
    if not results:
        st.info("Nenhum resultado disponivel. Processe alguns tickets na aba 'Processar Tickets'.")
        return

    col1, col2, col3 = st.columns(3)
    resolved = sum(1 for item in results if item["status"] == "Resolvido")
    escalated = sum(1 for item in results if "Escalado" in item["status"])
    errors = sum(1 for item in results if item["status"] == "Erro")

    col1.metric("Resolvidos", resolved)
    col2.metric("Escalados", escalated)
    col3.metric("Erros", errors)

    st.markdown("---")

    for result in results:
        status = result["status"]
        if status == "Resolvido":
            status_icon = ":white_check_mark:"
        elif "Escalado" in status:
            status_icon = ":warning:"
        elif status == "Erro":
            status_icon = ":x:"
        else:
            status_icon = ":information_source:"

        with st.expander(f"{status_icon} Ticket #{result['ticket_id']} - {result['title']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Status:** {status}")
                st.write(f"**Intencao:** {result.get('intent', 'N/A')}")

            with col2:
                st.write(f"**Sistema:** {result.get('system', 'N/A')}")

            if result.get("resolution"):
                st.write("**Resolucao:**")
                st.text(result["resolution"])

            if result.get("error"):
                st.error(f"**Erro:** {result['error']}")


def render_escalated_tab() -> None:
    """Lista os tickets que ainda precisam de acompanhamento manual."""
    st.header("Tickets escalados")
    st.markdown("Tickets que precisam de atencao manual da equipe de suporte.")

    results = st.session_state.get("results") or []
    escalated_tickets = [item for item in results if "Escalado" in item.get("status", "")]

    if not escalated_tickets:
        st.success("Nenhum ticket escalado! Todos os tickets foram resolvidos automaticamente.")
        return

    st.warning(f"**{len(escalated_tickets)} tickets** aguardando acao da equipe de suporte")
    st.markdown("---")

    for ticket in escalated_tickets:
        st.markdown(f"### Ticket #{ticket['ticket_id']}")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**Titulo:** {ticket['title']}")
            st.write(f"**Status:** {ticket['status']}")

        with col2:
            st.write(f"**Tipo:** {ticket.get('intent', 'N/A')}")
            st.write(f"**Sistema:** {ticket.get('system', 'N/A')}")

        with col3:
            priority = "Alta" if ticket.get("intent") in {"vpn_access", "system_access"} else "Media"
            st.write(f"**Prioridade:** {priority}")

        if ticket.get("resolution"):
            with st.expander("Detalhes da escalacao", expanded=True):
                st.info(ticket["resolution"])

        if ticket.get("error"):
            with st.expander("Erro na automacao", expanded=False):
                st.error(ticket["error"])

        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            st.button(f"Ver usuario", key=f"user_{ticket['ticket_id']}", disabled=True)
        with action_col2:
            st.button(f"Abrir ticket", key=f"open_{ticket['ticket_id']}", disabled=True)
        with action_col3:
            st.button(f"Marcar resolvido", key=f"resolve_{ticket['ticket_id']}", disabled=True)

        st.markdown("---")


def render_tabs(tickets: List[Ticket], auto_process: bool) -> None:
    """Renderiza o layout de quatro abas que organiza a aplicacao."""
    tab_ticket_list, tab_process, tab_results, tab_escalated = st.tabs(
        ["Lista de Tickets", "Processar Tickets", "Resultados", "Tickets Escalados"]
    )

    with tab_ticket_list:
        render_ticket_list_tab(tickets)

    with tab_process:
        process_tickets_tab(tickets, auto_process)

    with tab_results:
        render_results_tab()

    with tab_escalated:
        render_escalated_tab()


def main() -> None:
    """Inicializa a aplicacao Streamlit."""
    try:
        configure_page()
        require_api_key()
        tickets = load_open_tickets()
        auto_process = render_sidebar_summary(tickets)
        render_tabs(tickets, auto_process)
    except Exception as e:
        st.error(f"Erro fatal na aplicação: {e}")
        st.code(traceback.format_exc())
        st.stop()


if __name__ == "__main__":
    main()
