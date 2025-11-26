# utils.py
from datetime import datetime
from typing import List
from .models import Sala
from .service import initialize_state

# Validação e conversão de datas
def validar_data_br(s: str) -> bool:
    """
    Valida datas no formato DD/MM/AAAA.
    Aceita datas passadas, presentes ou futuras.
    Apenas verifica formato e existência da data.
    """
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return True
    except Exception:
        return False
    
def converter_data_br_para_iso(s: str) -> str | None:
    """
    Converte DD/MM/AAAA → YYYY-MM-DD.
    Retorna None se inválida.
    """
    try:
        d = datetime.strptime(s, "%d/%m/%Y").date()
        return d.isoformat()  # YYYY-MM-DD
    except Exception:
        return None
    
def converter_data_iso_para_br(data_iso: str) -> str:
    try:
        dt = datetime.strptime(data_iso, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return data_iso  # fallback

# Conversão de estado (salas <-> dict)
def salas_to_dict_state(salas: List[Sala]) -> dict:
    return {"salas": [s.to_dict() for s in salas]}

def dict_state_to_salas(data: dict) -> List[Sala]:
    try:
        if "salas" in data:
            return [Sala.from_dict(s) for s in data["salas"]]
    except Exception:
        print("⚠️ Erro ao carregar salas do estado. Inicializando padrão.")
    return initialize_state()

# Helpers de input validados
def input_numero_sala(prompt="Número da sala (1-5): ") -> int | None:
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("❌ Número inválido.")
        return None

def input_idade_minima(prompt="Idade mínima [0-18] (ou cancelar): ") -> int | None:
    while True:
        s = input(prompt).strip()
        if s.lower() == "cancelar": return None
        if s.isdigit() and 0 <= int(s) <= 18: return int(s)
        print("❌ A idade mínima deve ser entre 0 e 18.")

def input_data_futura(prompt="Data de saída (DD/MM/AAAA) [ou cancelar]: ") -> str | None:
    while True:
        s = input(prompt).strip()
        if s.lower() == "cancelar": return None
        try:
            d = datetime.strptime(s, "%d/%m/%Y")
            if d.date() <= datetime.now().date():
                print("❌ A data deve ser futura.")
                continue
            return d.strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Formato inválido. Use DD/MM/AAAA.")
