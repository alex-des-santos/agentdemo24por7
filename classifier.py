"""Camada de utilidades para classificacao e suporte ao pipeline de automacao."""

from typing import Dict, Tuple
import os
from openai import OpenAI


_CATEGORIES = [
    "login_email",
    "login_azure",
    "login_windows",
    "account_locked",
    "password_reset",
    "vpn_access",
    "system_access",
    "out_of_scope",
]


def _ensure_api_key() -> str:
    """Garante que a credencial esteja configurada (aceita MODEL_API_KEY ou OPENAI_API_KEY)."""
    val = os.getenv("OPENAI_API_KEY") or os.getenv("MODEL_API_KEY")
    if not val:
        raise RuntimeError(
            "Credencial do serviço de classificação ausente. Defina OPENAI_API_KEY ou MODEL_API_KEY."
        )
    # Normaliza para a lib oficial
    os.environ.setdefault("OPENAI_API_KEY", val)
    return val


def _client() -> OpenAI:
    """Retorna o cliente do serviço de classificação."""
    _ensure_api_key()
    return OpenAI()


def classify_ticket_intent(description: str, title: str) -> Tuple[str, str]:
    """Classifica a intencao de um ticket usando um serviço externo de classificação."""
    prompt = (
        "Você é um classificador de tickets de suporte de TI.\n\n"
        f"TÍTULO: {title}\n"
        f"DESCRIÇÃO: {description}\n\n"
        "Responda APENAS com UMA das categorias a seguir (sem explicações):\n"
        + "\n".join(f"- {c}" for c in _CATEGORIES)
        + "\n\nCategoria:"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=10,
        )
        content = (resp.choices[0].message.content or "").strip().lower()
        label = content.split()[0] if content else "out_of_scope"
        if label not in _CATEGORIES:
            label = "out_of_scope"
        return label, content
    except Exception as exc:
        print(f"Erro ao classificar: {exc}")
        return "out_of_scope", str(exc)


def analyze_automation_capability(ticket: Dict, intent: str) -> Tuple[bool, str]:
    """Determina se o playbook de automacao deve tratar o ticket usando análise inteligente."""
    prompt = (
        "Você é um especialista em automação de tickets de TI.\n\n"
        f"TICKET ID: {ticket.get('id')}\n"
        f"TÍTULO: {ticket.get('title')}\n"
        f"DESCRIÇÃO: {ticket.get('description')}\n"
        f"CATEGORIA IDENTIFICADA: {intent}\n\n"
        "CONTEXTO:\n"
        "- O sistema pode automatizar: desbloqueio de contas, reset de senhas (Email, Azure AD, Windows)\n"
        "- NÃO pode automatizar: configurações de VPN, aprovações de acesso, problemas complexos\n\n"
        "Analise se este ticket pode ser TOTALMENTE automatizado.\n\n"
        "Responda EXATAMENTE no formato:\n"
        "PODE_AUTOMATIZAR: [SIM ou NÃO]\n"
        "RAZÃO: [explicação breve em uma linha]"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
        )
        content = (resp.choices[0].message.content or "").strip()
        
        # Parse resposta
        lines = content.split("\n")
        can_automate = False
        reason = "Erro ao processar análise"
        
        for line in lines:
            if "PODE_AUTOMATIZAR:" in line:
                can_automate = "SIM" in line.upper()
            elif "RAZÃO:" in line or "RAZAO:" in line:
                reason = line.split(":", 1)[1].strip()
        
        return can_automate, reason
    except Exception as exc:
        print(f"Erro na análise de automação: {exc}")
        # Fallback para lógica simples
        automatable = intent in ["login_email", "login_azure", "login_windows", "account_locked", "password_reset"]
        fallback_reason = "Reset/desbloqueio automatizável" if automatable else "Requer análise manual"
        return automatable, fallback_reason


def extract_system_from_description(description: str, title: str) -> str:
    """Infere qual sistema esta afetado usando análise inteligente."""
    prompt = (
        "Você é um analista de sistemas de TI.\n\n"
        f"TÍTULO: {title}\n"
        f"DESCRIÇÃO: {description}\n\n"
        "Identifique qual sistema está afetado.\n\n"
        "Responda APENAS com UMA das opções:\n"
        "- Email\n"
        "- AD\n"
        "- Windows\n"
        "- Desconhecido\n\n"
        "Sistema:"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        content = (resp.choices[0].message.content or "").strip()
        system = content.split()[0] if content else "Desconhecido"
        
        valid_systems = ["Email", "AD", "Windows", "Desconhecido"]
        if system not in valid_systems:
            # Tentativa de match parcial
            system_lower = system.lower()
            if "email" in system_lower or "outlook" in system_lower:
                return "Email"
            elif "ad" in system_lower or "azure" in system_lower or "active" in system_lower:
                return "AD"
            elif "windows" in system_lower:
                return "Windows"
            return "Desconhecido"
        
        return system
    except Exception as exc:
        print(f"Erro ao extrair sistema: {exc}")
        # Fallback para heurística simples
        text = f"{title} {description}".lower()
        if any(k in text for k in ["email", "outlook"]):
            return "Email"
        if any(k in text for k in ["azure", "active directory", " ad "]):
            return "AD"
        if any(k in text for k in ["windows", "pc", "notebook"]):
            return "Windows"
        return "Desconhecido"


def generate_resolution_summary(actions: list) -> str:
    """Cria um resumo em topicos, legivel para humanos, das acoes do playbook."""
    return "\n".join(f"- {a}" for a in actions)


def generate_personalized_email(
    recipient_type: str,
    ticket: Dict,
    context: Dict
) -> Tuple[str, str]:
    """Gera assunto e corpo de email personalizados usando LLM.
    
    Args:
        recipient_type: "user", "manager" ou "team"
        ticket: Dados do ticket
        context: Contexto adicional (actions_summary, temp_password, reason, etc.)
    
    Returns:
        Tuple[subject, body]
    """
    ticket_id = ticket.get("id")
    title = ticket.get("title")
    requester = ticket.get("requester")
    requester_name = ticket.get("requester_name", requester)
    
    status = context.get("status", "resolvido")
    actions_summary = context.get("actions_summary", "")
    temp_password = context.get("temp_password")
    reason = context.get("reason", "")
    
    if recipient_type == "user":
        prompt = (
            "Você é um assistente de suporte de TI que gera emails amigáveis e profissionais.\n\n"
            f"Gere um email para o usuário sobre o ticket #{ticket_id}.\n\n"
            f"CONTEXTO:\n"
            f"- Título do ticket: {title}\n"
            f"- Status: {status}\n"
            f"- Ações realizadas:\n{actions_summary}\n"
        )
        if temp_password:
            prompt += f"\n- Senha temporária gerada: {temp_password}\n"
        if reason:
            prompt += f"\n- Motivo: {reason}\n"
        
        prompt += (
            "\n\nGere um email no formato:\n"
            "ASSUNTO: [assunto do email]\n"
            "CORPO:\n[corpo do email]\n\n"
            "O email deve ser:\n"
            "- Conciso e claro\n"
            "- Empático e profissional\n"
            "- Incluir apenas informações relevantes\n"
        )
        if temp_password:
            prompt += "- OBRIGATORIAMENTE incluir a senha temporária e instruções para trocá-la\n"
    
    elif recipient_type == "manager":
        prompt = (
            "Você é um assistente de suporte de TI que gera emails profissionais para gestores.\n\n"
            f"Gere um email informativo para o gestor sobre o ticket #{ticket_id} do colaborador {requester_name}.\n\n"
            f"CONTEXTO:\n"
            f"- Título do ticket: {title}\n"
            f"- Colaborador: {requester_name}\n"
            f"- Status: {status}\n"
            f"- Ações realizadas:\n{actions_summary}\n"
        )
        if reason:
            prompt += f"\n- Motivo: {reason}\n"
        
        prompt += (
            "\n\nGere um email no formato:\n"
            "ASSUNTO: [assunto do email]\n"
            "CORPO:\n[corpo do email]\n\n"
            "O email deve ser:\n"
            "- Objetivo e informativo\n"
            "- Profissional\n"
            "- Destacar que é apenas informativo, sem necessidade de ação\n"
        )
    
    elif recipient_type == "team":
        assigned_team = context.get("assigned_team", "Suporte N2")
        prompt = (
            "Você é um assistente de suporte de TI que gera emails internos de escalação.\n\n"
            f"Gere um email de escalação para a equipe {assigned_team} sobre o ticket #{ticket_id}.\n\n"
            f"CONTEXTO:\n"
            f"- Título do ticket: {title}\n"
            f"- Solicitante: {requester_name}\n"
            f"- Motivo da escalação:\n{reason}\n"
            "\n\nGere um email no formato:\n"
            "ASSUNTO: [assunto do email]\n"
            "CORPO:\n[corpo do email]\n\n"
            "O email deve ser:\n"
            "- Direto e objetivo\n"
            "- Conter todas as informações necessárias para a equipe agir\n"
            "- Tom profissional e técnico\n"
        )
    else:
        return "Notificação de Ticket", "Email não gerado - tipo de destinatário inválido"
    
    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        content = (resp.choices[0].message.content or "").strip()
        
        # Parse resposta
        if "ASSUNTO:" in content and "CORPO:" in content:
            parts = content.split("CORPO:", 1)
            subject_part = parts[0].replace("ASSUNTO:", "").strip()
            body = parts[1].strip()
            return subject_part, body
        else:
            # Fallback se formato não está correto
            return f"Ticket #{ticket_id} - Atualização", content
    
    except Exception as exc:
        print(f"Erro ao gerar email personalizado: {exc}")
        # Fallback para template simples
        if recipient_type == "user":
            subject = f"Ticket #{ticket_id} - {status.capitalize()}"
            body = f"Seu ticket foi {status}.\n\nDetalhes:\n{actions_summary}"
        elif recipient_type == "manager":
            subject = f"Ticket #{ticket_id} - {requester_name}"
            body = f"Ticket do colaborador {requester_name} foi {status}.\n\nAções:\n{actions_summary}"
        else:
            subject = f"Escalação - Ticket #{ticket_id}"
            body = f"Ticket #{ticket_id} escalado.\n\nMotivo:\n{reason}"
        
        return subject, body


def analyze_ticket_priority_and_complexity(ticket: Dict) -> Dict:
    """Avalia prioridade e complexidade do ticket usando LLM.
    
    Returns:
        Dict com priority ("low", "medium", "high", "critical") e complexity ("simple", "moderate", "complex")
    """
    prompt = (
        "Você é um analista de suporte de TI especializado em triagem de tickets.\n\n"
        f"TICKET #{ticket.get('id')}\n"
        f"TÍTULO: {ticket.get('title')}\n"
        f"DESCRIÇÃO: {ticket.get('description')}\n\n"
        "Avalie:\n"
        "1. PRIORIDADE - com base no impacto no negócio e urgência\n"
        "2. COMPLEXIDADE - com base na dificuldade de resolução\n\n"
        "Responda EXATAMENTE no formato:\n"
        "PRIORIDADE: [low, medium, high ou critical]\n"
        "COMPLEXIDADE: [simple, moderate ou complex]\n"
        "JUSTIFICATIVA: [explicação breve em uma linha]"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
        )
        content = (resp.choices[0].message.content or "").strip()
        
        # Parse resposta
        priority = "medium"
        complexity = "moderate"
        justification = "Avaliação automática"
        
        for line in content.split("\n"):
            if "PRIORIDADE:" in line:
                val = line.split(":", 1)[1].strip().lower()
                if val in ["low", "medium", "high", "critical"]:
                    priority = val
            elif "COMPLEXIDADE:" in line:
                val = line.split(":", 1)[1].strip().lower()
                if val in ["simple", "moderate", "complex"]:
                    complexity = val
            elif "JUSTIFICATIVA:" in line:
                justification = line.split(":", 1)[1].strip()
        
        return {
            "priority": priority,
            "complexity": complexity,
            "justification": justification
        }
    except Exception as exc:
        print(f"Erro ao avaliar prioridade/complexidade: {exc}")
        return {
            "priority": "medium",
            "complexity": "moderate",
            "justification": "Erro na avaliação automática"
        }


def diagnose_issue(ticket: Dict, system: str, user_info: Dict = None) -> Dict:
    """Analisa sintomas e sugere diagnósticos e ações usando LLM.
    
    Returns:
        Dict com diagnosis (texto), suggested_actions (lista) e confidence ("low", "medium", "high")
    """
    prompt = (
        "Você é um especialista em diagnóstico de problemas de TI.\n\n"
        f"TICKET #{ticket.get('id')}\n"
        f"TÍTULO: {ticket.get('title')}\n"
        f"DESCRIÇÃO: {ticket.get('description')}\n"
        f"SISTEMA AFETADO: {system}\n"
    )
    
    if user_info:
        prompt += f"USUÁRIO: {user_info.get('username', 'N/A')}\n"
        prompt += f"STATUS DA CONTA: {user_info.get('status', 'N/A')}\n"
    
    prompt += (
        "\nCom base nos sintomas descritos:\n"
        "1. Faça um diagnóstico do problema\n"
        "2. Sugira ações específicas de resolução\n"
        "3. Avalie sua confiança no diagnóstico\n\n"
        "Responda EXATAMENTE no formato:\n"
        "DIAGNÓSTICO: [descrição do problema identificado]\n"
        "AÇÕES:\n"
        "- [ação 1]\n"
        "- [ação 2]\n"
        "CONFIANÇA: [low, medium ou high]"
    )

    try:
        resp = _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        content = (resp.choices[0].message.content or "").strip()
        
        # Parse resposta
        diagnosis = "Problema não identificado"
        suggested_actions = []
        confidence = "medium"
        
        lines = content.split("\n")
        in_actions = False
        
        for line in lines:
            if "DIAGNÓSTICO:" in line or "DIAGNOSTICO:" in line:
                diagnosis = line.split(":", 1)[1].strip()
                in_actions = False
            elif "AÇÕES:" in line or "ACOES:" in line:
                in_actions = True
            elif "CONFIANÇA:" in line or "CONFIANCA:" in line:
                val = line.split(":", 1)[1].strip().lower()
                if val in ["low", "medium", "high"]:
                    confidence = val
                in_actions = False
            elif in_actions and line.strip().startswith("-"):
                action = line.strip()[1:].strip()
                if action:
                    suggested_actions.append(action)
        
        return {
            "diagnosis": diagnosis,
            "suggested_actions": suggested_actions,
            "confidence": confidence
        }
    except Exception as exc:
        print(f"Erro ao diagnosticar problema: {exc}")
        return {
            "diagnosis": "Erro ao executar diagnóstico automático",
            "suggested_actions": ["Encaminhar para análise manual"],
            "confidence": "low"
        }
