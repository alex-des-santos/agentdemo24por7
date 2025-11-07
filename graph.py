"""Nos do fluxo que orquestram o pipeline automatizado de tickets."""

from typing import TypedDict, Literal, List, Dict, Any
from langgraph.graph import StateGraph, END
from tools import ticket_manager, identity_service, email_service
from classifier import (
    classify_ticket_intent,
    analyze_automation_capability,
    extract_system_from_description,
    generate_resolution_summary,
    analyze_ticket_priority_and_complexity,
    diagnose_issue
)

class TicketState(TypedDict, total=False):
    """Estado compartilhado trocado entre os nos do LangGraph."""

    ticket: Dict[str, Any]
    intent: str
    intent_details: str
    system: str
    can_automate: bool
    automation_reason: str
    user_info: Dict[str, Any]
    actions_performed: List[str]
    playbook_result: Dict[str, Any]
    resolution_summary: str
    final_status: str
    error_message: str
    priority: str
    complexity: str
    priority_justification: str
    diagnosis: str
    suggested_actions: List[str]
    diagnosis_confidence: str

def node_classify_intent(state: TicketState) -> TicketState:
    """Aciona o classificador para inferir a intencao do ticket e persistir no estado."""
    ticket = state["ticket"]
    print(f"\n{'='*80}")
    print(f"STEP 1: Classificando intenção do Ticket #{ticket['id']}")
    print(f"{'='*80}")
    
    intent, details = classify_ticket_intent(ticket["description"], ticket["title"])
    
    print(f"Intenção identificada: {intent}")
    print(f"Detalhes: {details}")
    
    return {
        **state,
        "intent": intent,
        "intent_details": details
    }

def node_extract_system(state: TicketState) -> TicketState:
    """Detecta qual sistema e mencionado no ticket e salva a resposta."""
    ticket = state["ticket"]
    print(f"\n{'='*80}")
    print(f"STEP 2: Identificando sistema afetado")
    print(f"{'='*80}")
    
    system = extract_system_from_description(ticket["description"], ticket["title"])
    
    print(f"Sistema identificado: {system}")
    
    return {
        **state,
        "system": system
    }

def node_analyze_priority(state: TicketState) -> TicketState:
    """Avalia prioridade e complexidade do ticket."""
    ticket = state["ticket"]
    print(f"\n{'='*80}")
    print(f"STEP 2.5: Analisando prioridade e complexidade")
    print(f"{'='*80}")
    
    analysis = analyze_ticket_priority_and_complexity(ticket)
    
    print(f"Prioridade: {analysis['priority']}")
    print(f"Complexidade: {analysis['complexity']}")
    print(f"Justificativa: {analysis['justification']}")
    
    return {
        **state,
        "priority": analysis["priority"],
        "complexity": analysis["complexity"],
        "priority_justification": analysis["justification"]
    }

def node_diagnose(state: TicketState) -> TicketState:
    """Realiza diagnóstico inteligente do problema."""
    ticket = state["ticket"]
    system = state.get("system", "Desconhecido")
    user_info = state.get("user_info")
    
    print(f"\n{'='*80}")
    print(f"STEP 4.5: Realizando diagnóstico inteligente")
    print(f"{'='*80}")
    
    diagnosis_result = diagnose_issue(ticket, system, user_info)
    
    print(f"Diagnóstico: {diagnosis_result['diagnosis']}")
    print(f"Confiança: {diagnosis_result['confidence']}")
    print("Ações sugeridas:")
    for action in diagnosis_result['suggested_actions']:
        print(f"  - {action}")
    
    return {
        **state,
        "diagnosis": diagnosis_result["diagnosis"],
        "suggested_actions": diagnosis_result["suggested_actions"],
        "diagnosis_confidence": diagnosis_result["confidence"]
    }

def node_check_eligibility(state: TicketState) -> TicketState:
    """Decide se o ticket atual pode ser resolvido automaticamente."""
    intent = state["intent"]
    print(f"\n{'='*80}")
    print(f"STEP 3: Analisando capacidade de automação")
    print(f"{'='*80}")
    
    can_automate, reason = analyze_automation_capability(state["ticket"], intent)
    
    print(f"Pode automatizar? {can_automate}")
    print(f"Razão: {reason}")
    
    return {
        **state,
        "can_automate": can_automate,
        "automation_reason": reason
    }

def node_get_user_info(state: TicketState) -> TicketState:
    """Busca informacoes basicas do solicitante no servico de identidade."""
    ticket = state["ticket"]
    print(f"\n{'='*80}")
    print(f"STEP 4: Buscando informações do usuário")
    print(f"{'='*80}")
    
    user_info = identity_service.get_user(ticket["requester"])
    
    return {
        **state,
        "user_info": user_info
    }

def node_execute_playbook(state: TicketState) -> TicketState:
    """Executa o playbook automatizado para problemas de credenciais."""
    ticket = state["ticket"]
    user_info = state.get("user_info", {})
    system = state.get("system", "AD")
    intent = state.get("intent", "")
    
    print(f"\n{'='*80}")
    print(f"STEP 5: Executando playbook de resolução")
    print(f"{'='*80}")
    
    actions_performed = []
    playbook_result = {"ok": True, "actions": []}
    
    try:
        user_id = user_info.get("user_id", ticket["requester"].split("@")[0])
        
        if "locked" in intent or "login" in intent:
            lock_status = identity_service.check_user_locked(user_id)
            actions_performed.append(f"Verificação de bloqueio: {'Bloqueado' if lock_status.get('is_locked') else 'Desbloqueado'}")
            
            if lock_status.get("is_locked"):
                unlock_result = identity_service.unlock_user(user_id, system)
                if unlock_result.get("ok"):
                    actions_performed.append(f"Usuário desbloqueado no {system}")
                    playbook_result["actions"].append(unlock_result)
        
        if "password" in intent or "reset" in intent or "login" in intent:
            reset_result = identity_service.reset_password(user_id, system)
            if reset_result.get("ok"):
                actions_performed.append(f"Senha resetada no {system}")
                playbook_result["temp_password"] = reset_result.get("temp_password")
                playbook_result["actions"].append(reset_result)
        
        verify_result = identity_service.verify_user_unlocked(user_id, system)
        if verify_result.get("ok"):
            actions_performed.append(f"Verificação final: Usuário desbloqueado")
            playbook_result["actions"].append(verify_result)
        
        playbook_result["ok"] = True
        playbook_result["user_id"] = user_id
        
    except Exception as e:
        print(f"ERRO durante execução do playbook: {e}")
        playbook_result = {
            "ok": False,
            "error": str(e),
            "actions": []
        }
        actions_performed.append(f"ERRO: {str(e)}")
    
    return {
        **state,
        "actions_performed": actions_performed,
        "playbook_result": playbook_result
    }

def node_notify_and_update(state: TicketState) -> TicketState:
    """Persiste resultados da automacao, notifica envolvidos e encerra o ticket."""
    ticket = state["ticket"]
    playbook_result = state.get("playbook_result", {})
    actions_performed = state.get("actions_performed", [])
    
    print(f"\n{'='*80}")
    print(f"STEP 6: Notificando usuário e atualizando ticket")
    print(f"{'='*80}")
    
    if playbook_result.get("ok"):
        actions_summary = generate_resolution_summary(actions_performed)
        
        if playbook_result.get("temp_password"):
            actions_summary += f"\n\nSenha temporária: {playbook_result['temp_password']}"
            actions_summary += "\nPor favor, altere sua senha no primeiro login."
        
        comment = f"""Ticket resolvido automaticamente pelo sistema.

AÇÕES EXECUTADAS:
{actions_summary}

Data/Hora: {ticket_manager.add_comment.__module__}
Status: Resolvido
"""
        
        ticket_manager.add_comment(ticket["id"], comment)
        ticket_manager.set_status(ticket["id"], "Resolvido")
        
        resolution_details = {
            "actions_summary": actions_summary,
            "additional_info": f"Senha temporária: {playbook_result.get('temp_password', 'N/A')}" if playbook_result.get('temp_password') else ""
        }
        
        try:
            email_service.send_notification_to_user(
                ticket["requester"],
                ticket["id"],
                resolution_details
            )
        except Exception as e:
            print(f"AVISO: Falha ao enviar email para usuário: {e}")
            ticket_manager.add_comment(ticket["id"], f"AVISO: Não foi possível enviar email para {ticket['requester']}")
        
        if ticket.get("manager"):
            try:
                requester_name = ticket.get("requester_name", ticket.get("requester", "Usuário"))
                email_service.send_notification_to_manager(
                    ticket["manager"],
                    requester_name,
                    ticket["id"],
                    resolution_details
                )
            except Exception as e:
                print(f"AVISO: Falha ao enviar email para gestor: {e}")
                ticket_manager.add_comment(ticket["id"], f"AVISO: Não foi possível enviar email para gestor {ticket.get('manager')}")
        
        ticket_manager.add_action_log(
            ticket["id"],
            "Resolução Automática",
            {
                "actions": actions_performed,
                "temp_password_generated": bool(playbook_result.get("temp_password"))
            }
        )
        
        return {
            **state,
            "final_status": "Resolvido",
            "resolution_summary": actions_summary
        }
    else:
        error_msg = playbook_result.get("error", "Erro desconhecido")
        comment = f"""Tentativa de resolução automática falhou.

ERRO: {error_msg}

O ticket será escalado para análise manual.
"""
        
        ticket_manager.add_comment(ticket["id"], comment)
        ticket_manager.set_status(ticket["id"], "Escalado - Erro na Automação")
        
        escalation_info = {
            "actions_summary": f"Tentativa de automação falhou. Motivo: {error_msg}\n\nSeu ticket foi escalado para a equipe de suporte que entrará em contato em breve."
        }
        
        try:
            email_service.send_escalation_notification_to_user(
                ticket["requester"],
                ticket["id"],
                escalation_info
            )
        except Exception as e:
            print(f"AVISO: Falha ao enviar email para usuário durante escalação: {e}")
            ticket_manager.add_comment(ticket["id"], f"AVISO: Não foi possível enviar email para {ticket['requester']}")
        
        if ticket.get("manager"):
            try:
                requester_name = ticket.get("requester_name", ticket.get("requester", "Usuário"))
                email_service.send_escalation_notification_to_manager(
                    ticket["manager"],
                    requester_name,
                    ticket["id"],
                    escalation_info
                )
            except Exception as e:
                print(f"AVISO: Falha ao enviar email para gestor durante escalação: {e}")
                ticket_manager.add_comment(ticket["id"], f"AVISO: Não foi possível enviar email para gestor {ticket.get('manager')}")
        
        try:
            email_service.send_escalation_notification(
                ticket["id"],
                f"Falha na automação: {error_msg}",
                "Suporte N2"
            )
        except Exception as e:
            print(f"ERRO: Falha ao enviar notificação de escalação: {e}")
        
        return {
            **state,
            "final_status": "Escalado - Erro",
            "error_message": error_msg
        }

def node_escalate(state: TicketState) -> TicketState:
    """Documenta o motivo da escalacao e encaminha o ticket para humanos."""
    ticket = state["ticket"]
    reason = state.get("automation_reason", "Motivo não especificado")
    intent = state.get("intent", "desconhecido")
    
    print(f"\n{'='*80}")
    print(f"STEP 6: Escalando ticket (não automatizável)")
    print(f"{'='*80}")
    
    escalation_details = f"""Ticket não automatizável - Requer atenção manual

ANÁLISE:
- Tipo identificado: {intent}
- Motivo: {reason}

RECOMENDAÇÕES:
"""
    
    if intent == "vpn_access":
        escalation_details += "- Verificar configurações de VPN\n- Validar conexão de rede\n- Revisar logs de conexão"
    elif intent == "system_access":
        escalation_details += "- Validar permissões necessárias\n- Obter aprovação do gestor\n- Configurar acessos específicos"
    else:
        escalation_details += "- Análise detalhada necessária\n- Possível necessidade de intervenção especializada"
    
    ticket_manager.add_comment(ticket["id"], escalation_details)
    ticket_manager.set_status(ticket["id"], "Escalado para Suporte N2")
    
    user_notification = {
        "actions_summary": f"""Seu ticket foi analisado e precisa de atenção especializada.

Motivo: {reason}

A equipe de suporte entrará em contato em breve para resolver seu problema."""
    }
    
    try:
        email_service.send_escalation_notification_to_user(
            ticket["requester"],
            ticket["id"],
            user_notification
        )
    except Exception as e:
        print(f"AVISO: Falha ao enviar email para usuário na escalação: {e}")
        ticket_manager.add_comment(ticket["id"], f"AVISO: Não foi possível enviar email para {ticket['requester']}")
    
    if ticket.get("manager"):
        try:
            requester_name = ticket.get("requester_name", ticket.get("requester", "Usuário"))
            manager_notification = {
                "actions_summary": f"""O ticket do colaborador foi escalado para análise manual.

Tipo do problema: {intent}
Motivo da escalação: {reason}

A equipe de suporte está ciente e tomará as ações necessárias."""
            }
            email_service.send_escalation_notification_to_manager(
                ticket["manager"],
                requester_name,
                ticket["id"],
                manager_notification
            )
        except Exception as e:
            print(f"AVISO: Falha ao enviar email para gestor na escalação: {e}")
            ticket_manager.add_comment(ticket["id"], f"AVISO: Não foi possível enviar email para gestor {ticket.get('manager')}")
    
    try:
        email_service.send_escalation_notification(
            ticket["id"],
            escalation_details,
            "Suporte N2"
        )
    except Exception as e:
        print(f"ERRO: Falha ao enviar notificação de escalação: {e}")
    
    ticket_manager.add_action_log(
        ticket["id"],
        "Escalação Automática",
        {
            "intent": intent,
            "reason": reason
        }
    )
    
    return {
        **state,
        "final_status": "Escalado",
        "resolution_summary": escalation_details
    }

def route_after_eligibility(state: TicketState) -> Literal["get_user_info", "escalate"]:
    """Escolhe o proximo no com base na elegibilidade de automacao."""
    if state.get("can_automate", False):
        return "get_user_info"
    else:
        return "escalate"

def build_graph() -> StateGraph:
    """Compila o fluxo do LangGraph que sustenta o runbook de tickets."""
    builder = StateGraph(TicketState)
    
    builder.add_node("classify_intent", node_classify_intent)
    builder.add_node("extract_system", node_extract_system)
    builder.add_node("analyze_priority", node_analyze_priority)
    builder.add_node("check_eligibility", node_check_eligibility)
    builder.add_node("get_user_info", node_get_user_info)
    builder.add_node("diagnose", node_diagnose)
    builder.add_node("execute_playbook", node_execute_playbook)
    builder.add_node("notify_and_update", node_notify_and_update)
    builder.add_node("escalate", node_escalate)
    
    builder.set_entry_point("classify_intent")
    
    builder.add_edge("classify_intent", "extract_system")
    builder.add_edge("extract_system", "analyze_priority")
    builder.add_edge("analyze_priority", "check_eligibility")
    
    builder.add_conditional_edges(
        "check_eligibility",
        route_after_eligibility,
        {
            "get_user_info": "get_user_info",
            "escalate": "escalate"
        }
    )
    
    builder.add_edge("get_user_info", "diagnose")
    builder.add_edge("diagnose", "execute_playbook")
    builder.add_edge("execute_playbook", "notify_and_update")
    builder.add_edge("notify_and_update", END)
    builder.add_edge("escalate", END)
    
    return builder.compile()
