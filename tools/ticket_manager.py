"""Utilitários para leitura e registro de informações de tickets."""

# Imports de bibliotecas padrão para I/O, caminhos, datas e tipagem
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Caminho para o arquivo de dados de tickets utilizado como "banco" local
DATA_PATH = Path(__file__).parent.parent / "data" / "tickets.json"

def get_open_tickets() -> List[Dict]:
    """Return every ticket marked as open inside the local data store."""
    # Lê todos os tickets do arquivo JSON
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tickets = json.load(f)
    # Filtra apenas aqueles cujo status está marcado como "open"
    return [t for t in tickets if t.get("status") == "open"]

def get_ticket_by_id(ticket_id: int) -> Optional[Dict]:
    """Load a single ticket by id, returning None when it is absent."""
    # Carrega os tickets e procura um com o ID solicitado
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tickets = json.load(f)
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            # Retorna imediatamente quando encontra o ticket
            return ticket
    # Retorna None quando nenhum ticket corresponde ao ID
    return None

def add_comment(ticket_id: int, comment: str) -> Dict:
    """Log that a comment was attached to a ticket and echo the action."""
    # Gera um timestamp e formata uma entrada de log com o comentário
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [TICKET {ticket_id}] Comentario adicionado:\n{comment}\n"
    # Emite a linha de log no console para acompanhamento
    print(log_entry)
    # Retorna um objeto estruturado descrevendo a operação realizada
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "comment": comment,
        "timestamp": timestamp
    }

def set_status(ticket_id: int, status: str) -> Dict:
    """Record the new status assigned to a ticket."""
    # Registra a alteração de status com o horário do evento
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [TICKET {ticket_id}] Status alterado para: {status}"
    print(log_entry)
    # Retorna um payload com os metadados da alteração realizada
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "status": status,
        "timestamp": timestamp
    }

def add_action_log(ticket_id: int, action: str, details: Dict) -> Dict:
    """Document one automation action and its metadata in the logs."""
    # Consolida detalhes da ação em uma linha de log formatada
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [TICKET {ticket_id}] Acao: {action}\nDetalhes: {json.dumps(details, indent=2, ensure_ascii=False)}\n"
    print(log_entry)
    # Retorna um resumo estruturado da ação realizada
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "action": action,
        "details": details,
        "timestamp": timestamp
    }
