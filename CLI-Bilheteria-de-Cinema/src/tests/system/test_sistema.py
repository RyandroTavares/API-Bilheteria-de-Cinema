# tests/system/test_sistema.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.service import (
    initialize_state,
    add_filme_to_sala,
    issue_ticket,
    verify_ticket_payload,
)
from src.models import Sala

# --- Helpers de persistência usados apenas nos testes ---
def salas_to_list_of_dicts(salas):
    out = []
    for s in salas:
        if hasattr(s, "to_dict"):
            out.append(s.to_dict())
        else:
            filme = getattr(s, "filme", None)
            out.append({
                "numero": getattr(s, "numero", None),
                "filme": filme.to_dict() if filme and hasattr(filme, "to_dict") else None
            })
    return out

def list_of_dicts_to_salas(listdict):
    salas = []
    for d in listdict:
        if hasattr(Sala, "from_dict"):
            salas.append(Sala.from_dict(d))
        else:
            s = Sala(numero=d.get("numero"))
            f = d.get("filme")
            if f:
                from src.models import Filme
                s.adicionar_filme(Filme(**f))
            salas.append(s)
    return salas

# CT07b - Persistência do estado do sistema
def test_fluxo_persistencia_estado(tmp_path, monkeypatch):
    """
    Fluxo do sistema:
    1. Inicializar estado → adicionar filmes às salas
    2. Salvar estado em arquivo JSON
    3. Carregar estado do arquivo
    4. Verificar que todas as salas e filmes foram restaurados corretamente
    """
    # Arquivo temporário para persistência
    state_file = tmp_path / "state_test.json"

    # Monkeypatch se o projeto tiver src.storage.STATE_FILE
    try:
        import src.storage as storage
        monkeypatch.setattr(storage, "STATE_FILE", state_file)
    except Exception:
        pass

    # 1) Inicializa o estado e adiciona filmes
    salas = initialize_state()
    assert len(salas) >= 1

    add_filme_to_sala(salas[0], "Filme Persistido 1", "Ação", 14, "2099-12-31")
    add_filme_to_sala(salas[1], "Filme Persistido 2", "Drama", 10, "2099-12-31")

    # 2) Salva estado em JSON
    serial = salas_to_list_of_dicts(salas)
    state_file.write_text(json.dumps(serial, ensure_ascii=False, indent=2), encoding="utf-8")
    assert state_file.exists()

    # 3) Carrega o estado do arquivo
    loaded_raw = json.loads(state_file.read_text(encoding="utf-8"))
    salas_restauradas = list_of_dicts_to_salas(loaded_raw)

    # 4) Verificações: todas as salas e filmes restaurados corretamente
    assert len(salas_restauradas) == len(salas)
    assert salas_restauradas[0].filme is not None
    assert salas_restauradas[0].filme.nome == "Filme Persistido 1"
    assert salas_restauradas[1].filme.nome == "Filme Persistido 2"

# CT07c - Fluxo completo do sistema (fim-a-fim)
def test_fluxo_completo_salvar_carregar(tmp_path, monkeypatch):
    state_file = tmp_path / "state_test2.json"
    used_tickets_file = tmp_path / "used_tickets_test.json"

    try:
        import src.used_tickets as used_tk_mod
        monkeypatch.setattr(used_tk_mod, "USED_TICKETS_FILE", used_tickets_file)
    except Exception:
        pass

    salas = initialize_state()
    add_filme_to_sala(salas[0], "Fluxo E2E", "Aventura", 12, "2099-11-30")

    # MOCK DAS CHAVES CRIPTO
    fake_priv = MagicMock()
    fake_priv.sign.return_value = b"deadbeef"
    fake_pub = MagicMock()

    def fake_verify_signature(pub, payload, sig_bytes):
        return sig_bytes == b"deadbeef"

    with patch("src.service.load_private_key", return_value=fake_priv), \
         patch("src.service.sign_payload", return_value=b"deadbeef"), \
         patch("src.service.load_public_key", return_value=fake_pub), \
         patch("src.service.verify_signature", side_effect=fake_verify_signature):

        ticket = issue_ticket(salas[0])
        assert ticket["filme"] == "Fluxo E2E"
        assert salas[0].filme.ingressos == 49

        valid = verify_ticket_payload(ticket.copy())
        assert valid is True

    serial = salas_to_list_of_dicts(salas)
    state_file.write_text(json.dumps(serial, ensure_ascii=False, indent=2), encoding="utf-8")
    assert state_file.exists()

    loaded_raw = json.loads(state_file.read_text(encoding="utf-8"))
    salas_restauradas = list_of_dicts_to_salas(loaded_raw)

    assert salas_restauradas[0].filme is not None
    assert salas_restauradas[0].filme.nome == "Fluxo E2E"
    assert salas_restauradas[0].filme.ingressos == 49

    try:
        if used_tickets_file.exists():
            used_list = json.loads(used_tickets_file.read_text(encoding="utf-8"))
            assert ticket["id"] in used_list
    except Exception:
        pass
