import pytest
from unittest.mock import patch
from src.service import initialize_state, add_filme_to_sala, remove_filme_from_sala
import src.cli as cli
from src.cli import save_state_interactive, load_state_interactive, STATE_FILE

# CT07: Salvar e restaurar estado
def test_salvar_e_restaurar_estado():
    state = initialize_state()
    add_filme_to_sala(state[0], "Filme 1", "Ação", 12, "2025-12-31")
    add_filme_to_sala(state[1], "Filme 2", "Comédia", 10, "2025-12-31")

    # Patch correto do getpass no namespace do cli
    with patch.object(cli, "getpass", return_value="teste123"):
        save_state_interactive(state)
        restored_state = load_state_interactive()

    # Verifica integridade
    assert len(restored_state) == 5
    assert restored_state[0].filme.nome == "Filme 1"
    assert restored_state[1].filme.nome == "Filme 2"
    for s in restored_state[2:]:
        assert s.filme is None

    # Limpeza do arquivo de estado
    if STATE_FILE.exists():
        STATE_FILE.unlink()


# CT07a: Integridade após várias operações
def test_integridade_apos_varias_operacoes():
    state = initialize_state()

    # Adiciona filmes
    add_filme_to_sala(state[0], "Filme A", "Ação", 12, "2025-12-31")
    add_filme_to_sala(state[1], "Filme B", "Comédia", 10, "2025-12-31")

    # Remove filme da segunda sala
    remove_filme_from_sala(state[1])

    # Adiciona outro filme na terceira sala
    add_filme_to_sala(state[2], "Filme C", "Drama", 14, "2025-12-31")

    # Verifica integridade
    assert state[0].filme.nome == "Filme A"
    assert state[1].filme is None
    assert state[2].filme.nome == "Filme C"
    for s in state[3:]:
        assert s.filme is None
