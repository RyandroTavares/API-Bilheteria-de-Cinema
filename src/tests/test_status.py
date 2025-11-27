import pytest
from src.models import Sala
from src.service import add_filme_to_sala

# CT04 - Status inicial
def test_status_salas_vazias():
    salas = [Sala(numero=i+1) for i in range(5)]
    for s in salas:
        assert s.filme is None

# CT04a - Status após alterações
def test_status_apos_operacoes():
    salas = [Sala(numero=i+1) for i in range(5)]
    add_filme_to_sala(salas[0], "Filme 1", "Ação", 12, "2025-12-31")
    assert salas[0].filme.nome == "Filme 1"
