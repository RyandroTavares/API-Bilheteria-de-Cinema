import pytest
from src.models import Sala
from src.service import add_filme_to_sala, remove_filme_from_sala

# Testes RF01 – Adição de Filmes
@pytest.fixture
def sala_vazia():
    """Cria uma sala vazia para testes."""
    return Sala(numero=1)

# CT01 - Adição de filme válido (ISO e BR)
def test_adicionar_filme_valido(sala_vazia):
    add_filme_to_sala(sala_vazia, "Filme ISO", "Ação", 12, "2025-12-31")
    assert sala_vazia.filme is not None
    assert sala_vazia.filme.nome == "Filme ISO"
    assert sala_vazia.filme.ingressos == 50

# Testa formato BR
    add_filme_to_sala(sala_vazia, "Filme BR", "Drama", 14, "31/12/2025")
    assert sala_vazia.filme.nome == "Filme BR"
    assert sala_vazia.filme.ingressos == 50
    # Confirma que data foi convertida para ISO
    assert sala_vazia.filme.data_saida == "2025-12-31"

# CT01a1 - Adicionar filme com idade negativa (inválido)
def test_adicionar_filme_idade_negativa():
    sala = Sala(numero=1)
    # Idade mínima negativa
    with pytest.raises(ValueError):
        add_filme_to_sala(sala, "Filme Inválido", "Ação", -5, "2025-12-31")

# CT01a2 - Adicionar filme com data inválida
def test_adicionar_filme_data_invalida():
    sala = Sala(numero=1)
    # Data inválida (formato incorreto)
    with pytest.raises(ValueError):
        add_filme_to_sala(sala, "Filme Inválido", "Ação", 12, "31-12-2025")

    # Data futura inválida
    with pytest.raises(ValueError):
        add_filme_to_sala(sala, "Filme Inválido", "Ação", 12, "30-02-2026")

    # Data anterior ao dia atual
    with pytest.raises(ValueError):
        add_filme_to_sala(sala, "Filme Inválido", "Ação", 12, "2000-01-01")

# CT01a3 - Adicionar filme com nome vazio (inválido)
def test_adicionar_filme_nome_vazio():
    sala = Sala(numero=1)
    # Nome vazio
    with pytest.raises(ValueError):
        add_filme_to_sala(sala, "", "Ação", 12, "2025-12-31")

# CT01a4 - Adicionar filme com gênero vazio (inválido)
def test_adicionar_filme_genero_vazio():
    sala = Sala(numero=1)
    # Gênero vazio
    with pytest.raises(ValueError):
        add_filme_to_sala(sala, "Filme Inválido", "", 12, "2025-12-31")

# CT01b - Adição quando já existe filme (substituição)
def test_adicionar_filme_substituicao(sala_vazia):
    add_filme_to_sala(sala_vazia, "Filme 1", "Ação", 12, "2025-12-31")
    assert sala_vazia.filme.nome == "Filme 1"

    # Adiciona novo filme substituindo o existente
    add_filme_to_sala(sala_vazia, "Filme 2", "Comédia", 10, "31/12/2025")
    assert sala_vazia.filme.nome == "Filme 2"
    assert sala_vazia.filme.ingressos == 50
    # Verifica conversão da data BR para ISO
    assert sala_vazia.filme.data_saida == "2025-12-31"

# CT02 - Remoção de filme
def test_remover_filme(sala_vazia):
    add_filme_to_sala(sala_vazia, "Filme Teste", "Ação", 12, "2025-12-31")
    remove_filme_from_sala(sala_vazia)
    assert sala_vazia.filme is None

# CT02a - Remover filme inexistente
def test_remover_filme_vazio(sala_vazia):
    remove_filme_from_sala(sala_vazia) # não deve lançar erro
    assert sala_vazia.filme is None
