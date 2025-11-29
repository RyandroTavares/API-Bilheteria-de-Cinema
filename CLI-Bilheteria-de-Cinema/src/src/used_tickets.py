import json
from pathlib import Path

USED_TICKETS_FILE = Path(__file__).resolve().parent.parent / "data" / "used_tickets.json"

def load_used_tickets() -> set:
    """Carrega o conjunto de tickets já utilizados (IDs) do arquivo data/used_tickets.json."""
    try:
        if not USED_TICKETS_FILE.exists():
            return set()
        data = json.loads(USED_TICKETS_FILE.read_text(encoding="utf-8") or "[]")
        return set(data)
    except Exception:
        # Em caso de arquivo corrompido ou outra falha, retorna vazio (evita quebrar a CLI)
        return set()

def save_used_tickets(used: set):
    """Salva o conjunto de tickets usados no arquivo (lista JSON)."""
    try:
        USED_TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        USED_TICKETS_FILE.write_text(json.dumps(list(used), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        # Não interrompe a validação, mas registra no stdout
        print(f"⚠️ Falha ao salvar registro de tickets usados: {e}")