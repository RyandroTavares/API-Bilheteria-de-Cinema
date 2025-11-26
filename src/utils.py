from datetime import datetime, date

def validar_data_br(s: str) -> bool:
    """
    Valida datas no formato DD/MM/AAAA.
    Aceita datas passadas, presentes ou futuras.
    Apenas verifica:
      - formato correto
      - data existente (ex: 31/02 inválido)
    """
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return True
    except Exception:
        return False
    
def converter_data_br_para_iso(s: str) -> str:
    """
    Converte DD/MM/AAAA → YYYY-MM-DD.
    Retorna None se inválida.
    """
    try:
        d = datetime.strptime(s, "%d/%m/%Y").date()
        return d.isoformat()  # YYYY-MM-DD
    except Exception:
        return None