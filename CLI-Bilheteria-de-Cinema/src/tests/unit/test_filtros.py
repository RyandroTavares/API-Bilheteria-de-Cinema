import pytest
from src.models import Sala
from src.service import add_filme_to_sala, filter_salas

# CT05 - Filtrar por nome e datas
def test_filtrar_por_nome_e_data():
    salas = [Sala(numero=1), Sala(numero=2)]
    add_filme_to_sala(salas[0], "Aventura", "Ação", 12, "2025-12-31")
    add_filme_to_sala(salas[1], "Comédia", "Comédia", 10, "2025-11-30")
    resultados = filter_salas(salas, nome_parcial="Aventura")
    assert len(resultados) == 1
    assert resultados[0].filme.nome == "Aventura"

# CT05a - Nenhuma sala corresponde
def test_filtrar_nenhuma_corresponde():
    salas = [Sala(numero=1)]
    add_filme_to_sala(salas[0], "Aventura", "Ação", 12, "2025-12-31")
    resultados = filter_salas(salas, nome_parcial="Drama")
    assert resultados == []

# CT05b - Retornando múltiplas salas
def test_filtrar_multiplas_salas():
    salas = [Sala(numero=1), Sala(numero=2)]
    add_filme_to_sala(salas[0], "Aventura", "Ação", 12, "2025-12-31")
    add_filme_to_sala(salas[1], "Aventura 2", "Comédia", 10, "2025-12-31")
    resultados = filter_salas(salas, nome_parcial="Aventura")
    assert len(resultados) == 2
