import pytest
from unittest.mock import MagicMock, patch
from src.models import Sala
from src.service import add_filme_to_sala, issue_ticket

# CT03 - Emissão de ingresso normal
def test_emitir_ticket_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key
        ticket = issue_ticket(sala)

    assert ticket["filme"] == "Filme Teste"
    assert sala.filme.ingressos == 49  # 50 - 1

# CT03a - Emissão com ingressos zerados
def test_emitir_ticket_sem_ingressos_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")
    sala.filme.ingressos = 0

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        with pytest.raises(ValueError):
            issue_ticket(sala)

# CT03b - Emissão considerando idade mínima
def test_emitir_ticket_idade_minima_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Adulto", "Drama", 16, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        ticket = issue_ticket(sala)

    assert ticket["filme"] == "Filme Adulto"
    assert sala.filme.ingressos == 49

# CT03c - Simulando idade maior que mínima (mesmo comportamento do service)
def test_emitir_ticket_idade_invalida_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Adulto", "Drama", 18, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        ticket = issue_ticket(sala)

    assert ticket["filme"] == "Filme Adulto"
    assert sala.filme.ingressos == 49

# CT03d - Limite de ingressos: decremento para 0 e erro na próxima emissão
def test_emitir_ticket_ultimo_ingresso():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")

    # Ajusta ingressos para 1
    sala.filme.ingressos = 1

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        # Emite o último ingresso
        ticket = issue_ticket(sala)
        assert sala.filme.ingressos == 0  # decremento para 0

        # Próxima emissão deve falhar
        with pytest.raises(ValueError):
            issue_ticket(sala)
