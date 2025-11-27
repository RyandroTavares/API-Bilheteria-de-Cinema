import pytest
from src.models import Sala
from src.service import initialize_state, add_filme_to_sala

# CT07 - Salvar e restaurar estado
def test_estado_inicial():
    salas = initialize_state()
    assert len(salas) == 5
    for s in salas:
        assert s.filme is None

# CT07a - Integridade após várias operações
def test_estado_integridade():
    salas = initialize_state()
    add_filme_to_sala(salas[0], "Filme 1", "Ação", 12, "2025-12-31")
    add_filme_to_sala(salas[1], "Filme 2", "Comédia", 10, "2025-12-31")
    assert salas[0].filme.nome == "Filme 1"
    assert salas[1].filme.nome == "Filme 2"
