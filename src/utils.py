from datetime import datetime, date

def validar_data_iso(s: str) -> bool:
    try:
        d = datetime.strptime(s, "%d/%m/%Y").date()
        return d >= date.today()
    except Exception:
        return False