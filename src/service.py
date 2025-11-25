from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import uuid

from .models import Sala, Filme
from .crypto_keys import load_private_key, sign_payload

# Inicialização do estado padrão com 5 salas vazias
STATE_DEFAULT = {"salas": [Sala(numero=i+1).to_dict() for i in range(5)]}

def initialize_state() -> List[Sala]:
    """Inicializa e converte o estado padrão para objetos Sala."""
    return [Sala.from_dict(s) for s in STATE_DEFAULT["salas"]]

def find_sala(state: List[Sala], numero: int) -> Optional[Sala]:
    """Encontra uma sala pelo número."""
    try:
        numero = int(numero)
    except (ValueError, TypeError):
        return None
        
    for sala in state:
        if sala.numero == numero:
            return sala
    return None

def add_filme_to_sala(sala: Sala, nome: str, genero: str, idade_minima: int, data_saida: str):
    """Adiciona ou atualiza um filme em uma sala, garantindo 50 ingressos iniciais."""
    if not isinstance(sala, Sala):
        raise TypeError("O objeto passado deve ser do tipo Sala.")
        
    filme = Filme(
        nome=nome,
        genero=genero,
        idade_minima=idade_minima,
        ingressos=50,
        data_saida=data_saida  # Deve ser no formato ISO YYYY-MM-DD
    )
    sala.adicionar_filme(filme)

def remove_filme_from_sala(sala: Sala):
    """Remove um filme de uma sala."""
    if not isinstance(sala, Sala):
        raise TypeError("O objeto passado deve ser do tipo Sala.")
    sala.remover_filme()

def issue_ticket(sala: Sala) -> Dict[str, Any]:
    """
    Emite um ticket e assina o payload.
    Retorna o ticket com a assinatura.
    """
    if sala.esta_vazia():
        raise ValueError("Sala vazia ou inexistente.")
    
    if sala.filme.ingressos <= 0:
        raise ValueError("Ingressos esgotados.")

    # 1. Decrementa o ingresso
    sala.filme.ingressos -= 1
    
    # 2. Gera o ticket (payload)
    ticket_payload = {
        "id": uuid.uuid4().hex,
        "sala": sala.numero,
        "filme": sala.filme.nome,
        "emissao": datetime.now(timezone.utc).isoformat(),
        "assento": None
    }
    
    # 3. Assina o ticket
    priv_key = load_private_key()
    if not priv_key:
        raise PermissionError("Chave privada indisponível. Emissão cancelada.")

    # Serializa o payload, garantindo ordem das chaves para consistência da assinatura
    payload_to_sign = json.dumps(ticket_payload, sort_keys=True, ensure_ascii=False).encode()
    
    signature = sign_payload(priv_key, payload_to_sign)
    
    # 4. Adiciona a assinatura ao ticket
    ticket_payload["assinatura"] = signature.hex() # Converte para hex para serialização JSON

    return ticket_payload

def filter_salas(state: List[Sala], nome_parcial: str = "", data_de: str = "", data_ate: str = "") -> List[Dict[str, Any]]:
    """
    Filtra as salas baseadas em nome e datas.
    Retorna uma lista de dicionários para exibição.
    """
    results = []
    nome_lower = nome_parcial.strip().lower()

    for sala in state:
        f = sala.filme
        if not f:
            continue
        
        # Filtro por Nome
        if nome_lower and nome_lower not in f.nome.lower():
            continue
            
        # Filtro por Data 'De' (saída deve ser >= data_de)
        if data_de and f.data_saida < data_de:
            continue
            
        # Filtro por Data 'Até' (saída deve ser <= data_ate)
        if data_ate and f.data_saida > data_ate:
            continue

        # Adiciona à lista de resultados formatados
        results.append({
            "numero": sala.numero,
            "nome": f.nome,
            "data_saida": f.data_saida,
            "ingressos": f.ingressos
        })
        
    return results

def reset_state() -> List[Sala]:
    """Reseta o estado para o padrão inicial."""
    return initialize_state()