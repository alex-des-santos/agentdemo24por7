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
    """Determina se o playbook de automacao deve tratar o ticket."""
    automatable_intents = {
        "login_email": "Desbloqueio e reset de senha para email",
        "login_azure": "Desbloqueio de conta Azure AD e reset de senha",
        "login_windows": "Reset de senha do Windows e desbloqueio",
        "account_locked": "Desbloqueio de conta nos sistemas suportados",
        "password_reset": "Reset de senha nos sistemas suportados",
    }

    if intent in automatable_intents:
        return True, automatable_intents[intent]

    non_automatable_reasons = {
        "vpn_access": "Problemas de VPN requerem diagnóstico de rede e configuração específica",
        "system_access": "Acesso a sistemas específicos requer aprovação manual e verificação de permissões",
        "out_of_scope": "Problema fora do escopo de automação atual",
    }

    reason = non_automatable_reasons.get(intent, "Tipo de problema não suportado pela automação")
    return False, reason


def extract_system_from_description(description: str, title: str) -> str:
    """Infere qual sistema esta afetado (heurística simples)."""
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
