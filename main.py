"""Entrada via linha de comando do processador automatizado de tickets."""

from tools import ticket_manager
from graph import build_graph
import os

def main():
    """Executa todo o fluxo de automacao para cada ticket em aberto."""
    print("\n" + "="*80)
    print("SISTEMA AUTOMÁTICO DE GERENCIAMENTO DE TICKETS")
    print("="*80 + "\n")
    
    # Nao eh necessario validar credenciais: a demonstracao nao depende de servicos externos.
    
    tickets = ticket_manager.get_open_tickets()
    
    if not tickets:
        print("Nenhum ticket aberto encontrado.")
        return
    
    print(f"Encontrados {len(tickets)} tickets abertos para processamento.\n")
    
    app = build_graph()
    
    for idx, ticket in enumerate(tickets, 1):
        print("\n" + "#"*80)
        print(f"PROCESSANDO TICKET {idx}/{len(tickets)}")
        print(f"ID: {ticket['id']} | Título: {ticket['title']}")
        print(f"Solicitante: {ticket['requester_name']} ({ticket['requester']})")
        print("#"*80 + "\n")
        
        try:
            state = {"ticket": ticket}
            result = app.invoke(state)
            
            print(f"\n{'='*80}")
            print(f"RESULTADO DO PROCESSAMENTO - Ticket #{ticket['id']}")
            print(f"{'='*80}")
            print(f"Status Final: {result.get('final_status', 'Desconhecido')}")
            print(f"Intenção Identificada: {result.get('intent', 'N/A')}")
            print(f"Sistema: {result.get('system', 'N/A')}")
            
            if result.get('resolution_summary'):
                print(f"\nResumo da Resolução:")
                print(result['resolution_summary'])
            
            if result.get('error_message'):
                print(f"\nErro: {result['error_message']}")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\nERRO ao processar ticket #{ticket['id']}: {e}")
            print(f"{'='*80}\n")
    
    print("\n" + "="*80)
    print("PROCESSAMENTO CONCLUÍDO")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
