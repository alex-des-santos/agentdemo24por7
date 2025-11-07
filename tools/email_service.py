"""Utilitários simulados de e-mail usados pelo fluxo automatizado de tickets."""

# Imports das bibliotecas padrão usados para registrar timestamps e tipos de retorno
from datetime import datetime
from typing import Dict, Optional
import os

def send_email(to: str, subject: str, body: str, cc: Optional[str] = None) -> Dict:
    """Simula o envio de um e-mail e registra o conteúdo."""
    # Captura um timestamp legível para acompanhar quando o "envio" ocorreu
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Bloco de log: imprime um cabeçalho visual e metadados do email
    print(f"\n{'='*80}")
    print(f"[{timestamp}] [EMAIL SERVICE] Enviando email...")
    print(f"{'='*80}")

    # Destinatários e assunto (imprime CC somente se informado)
    print(f"Para    : {to}")
    if cc:
        # CC é opcional; apresenta somente quando fornecido
        print(f"CC      : {cc}")
    print(f"Assunto : {subject}")

    # Bloco de corpo: mostra o conteúdo textual enviado
    print(f"{'='*80}")
    print("Corpo do email:")
    print(body)
    print(f"{'='*80}\n")

    # Retorna um resumo estruturado da operação para consumo por outros componentes
    return {
        "ok": True,
        "to": to,
        "cc": cc,
        "subject": subject,
        "sent_at": timestamp,
        "message": "Email enviado com sucesso"
    }

def send_notification_to_user(user_email: str, ticket_id: int, resolution_details: Dict) -> Dict:
    """Notifica o solicitante que o ticket foi resolvido automaticamente."""
    # Tenta gerar email personalizado via LLM se disponível
    use_llm = os.getenv("USE_LLM_EMAILS", "true").lower() == "true"
    
    if use_llm:
        try:
            from classifier import generate_personalized_email
            
            # Constrói contexto do ticket
            ticket = {
                "id": ticket_id,
                "title": resolution_details.get("title", "Problema de acesso"),
                "requester": user_email,
            }
            context = {
                "status": "resolvido",
                "actions_summary": resolution_details.get('actions_summary', 'Ações executadas'),
                "temp_password": resolution_details.get('temp_password'),
            }
            
            subject, body = generate_personalized_email("user", ticket, context)
            return send_email(user_email, subject, body)
        except Exception as e:
            print(f"Erro ao gerar email via LLM, usando template padrão: {e}")
    
    # Fallback: template estático
    subject = f"Ticket #{ticket_id} - Problema Resolvido"
    body = f"""
Olá,

Seu ticket de suporte foi resolvido automaticamente pelo nosso sistema.

DETALHES DO TICKET:
- ID: #{ticket_id}
- Status: Resolvido

AÇÕES REALIZADAS:
{resolution_details.get('actions_summary', 'Ações de resolução executadas com sucesso')}

{resolution_details.get('additional_info', '')}

Se você ainda estiver enfrentando problemas, por favor, abra um novo ticket.

Atenciosamente,
Sistema Automático de Suporte
"""
    return send_email(user_email, subject, body)

def send_notification_to_manager(manager_email: str, user_name: str, ticket_id: int, resolution_details: Dict) -> Dict:
    """Informa ao gestor que o ticket do solicitante foi resolvido."""
    use_llm = os.getenv("USE_LLM_EMAILS", "true").lower() == "true"
    
    if use_llm:
        try:
            from classifier import generate_personalized_email
            
            ticket = {
                "id": ticket_id,
                "title": resolution_details.get("title", "Problema de acesso"),
                "requester_name": user_name,
            }
            context = {
                "status": "resolvido",
                "actions_summary": resolution_details.get('actions_summary', 'Ações executadas'),
            }
            
            subject, body = generate_personalized_email("manager", ticket, context)
            return send_email(manager_email, subject, body)
        except Exception as e:
            print(f"Erro ao gerar email via LLM para gestor, usando template padrão: {e}")
    
    # Fallback: template estático
    subject = f"Notificação: Ticket #{ticket_id} resolvido para {user_name}"
    body = f"""
Olá,

Informamos que o ticket de suporte do colaborador {user_name} foi resolvido automaticamente.

DETALHES:
- Ticket ID: #{ticket_id}
- Usuário: {user_name}
- Status: Resolvido automaticamente

AÇÕES REALIZADAS:
{resolution_details.get('actions_summary', 'Ações de resolução executadas')}

Este é um email informativo. Nenhuma ação adicional é necessária.

Atenciosamente,
Sistema Automático de Suporte
"""
    return send_email(manager_email, subject, body)

def send_escalation_notification_to_user(user_email: str, ticket_id: int, escalation_details: Dict) -> Dict:
    """Alerta o solicitante quando o ticket é escalado pela automação."""
    # Assunto indicando que o ticket foi escalado para análise manual
    subject = f"Ticket #{ticket_id} - Escalado para Análise"

    # Corpo explicando o status e o próximo passo para o solicitante
    body = f"""
Olá,

Seu ticket de suporte foi analisado e precisa de atenção especializada.

DETALHES DO TICKET:
- ID: #{ticket_id}
- Status: Escalado para equipe de suporte

INFORMAÇÕES:
{escalation_details.get('actions_summary', 'Seu ticket está sendo analisado pela equipe de suporte')}

A equipe de suporte entrará em contato em breve para resolver seu problema.

Atenciosamente,
Sistema Automático de Suporte
"""

    # Dispara o email ao usuário
    return send_email(user_email, subject, body)

def send_escalation_notification_to_manager(manager_email: str, user_name: str, ticket_id: int, escalation_details: Dict) -> Dict:
    """Notifica o gestor sobre tickets escalados que precisam de atenção."""
    # Assunto de escalonamento destinado ao gestor
    subject = f"Notificação: Ticket #{ticket_id} escalado - {user_name}"

    # Corpo com os metadados da escalada para acompanhamento do gestor
    body = f"""
Olá,

Informamos que o ticket de suporte do colaborador {user_name} foi escalado para análise manual.

DETALHES:
- Ticket ID: #{ticket_id}
- Usuário: {user_name}
- Status: Escalado para equipe de suporte

INFORMAÇÕES:
{escalation_details.get('actions_summary', 'Ticket escalado para análise especializada')}

A equipe de suporte está ciente e tomará as ações necessárias.

Este é um email informativo. Nenhuma ação adicional é necessária no momento.

Atenciosamente,
Sistema Automático de Suporte
"""

    # Envia a notificação ao gestor
    return send_email(manager_email, subject, body)

def send_escalation_notification(ticket_id: int, reason: str, assigned_team: str = "Suporte N2") -> Dict:
    """Envia o e-mail interno de escalação para a equipe responsável."""
    use_llm = os.getenv("USE_LLM_EMAILS", "true").lower() == "true"
    
    if use_llm:
        try:
            from classifier import generate_personalized_email
            
            ticket = {
                "id": ticket_id,
                "title": "Ticket escalado",
                "requester_name": "Usuário",
            }
            context = {
                "reason": reason,
                "assigned_team": assigned_team,
            }
            
            subject, body = generate_personalized_email("team", ticket, context)
            return send_email(f"{assigned_team.lower().replace(' ', '_')}@empresa.com", subject, body)
        except Exception as e:
            print(f"Erro ao gerar email de escalação via LLM, usando template padrão: {e}")
    
    # Fallback: template estático
    subject = f"Ticket #{ticket_id} - Escalado para {assigned_team}"
    body = f"""
ESCALAÇÃO DE TICKET

Ticket ID: #{ticket_id}
Escalado para: {assigned_team}

MOTIVO DA ESCALAÇÃO:
{reason}

Por favor, revisar e tomar ação apropriada.

Sistema Automático de Suporte
"""
    return send_email(f"{assigned_team.lower().replace(' ', '_')}@empresa.com", subject, body)
