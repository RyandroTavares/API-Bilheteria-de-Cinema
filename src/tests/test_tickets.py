import pytest
from unittest.mock import MagicMock, patch
from src import used_tickets
from src.models import Sala
from src.service import add_filme_to_sala, issue_ticket, verify_ticket_payload

# Após cada teste limpa a lista de tickets (used_tickets.json)
@pytest.fixture(autouse=True)
def clear_used_tickets_file_after():
    """Limpa o arquivo de tickets usados após cada teste."""
    yield  # deixa o teste rodar
    if used_tickets.USED_TICKETS_FILE.exists():
        used_tickets.USED_TICKETS_FILE.write_text("[]", encoding="utf-8")

# CT06 - Ticket válido
def test_ticket_valido_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        ticket = issue_ticket(sala)

    # Mock da verificação da assinatura
    with patch("src.service.load_public_key") as mock_pub:
        mock_pub.return_value = MagicMock()
        mock_pub.return_value.verify.return_value = True
        assert verify_ticket_payload(ticket) is True
        assert sala.filme.ingressos == 49  # 50 - 1

# CT06a - Ticket inválido (assinatura falsa)
def test_ticket_invalido_mock():
    ticket_falso = {
        "id": "1234567890abcdef",
        "sala": 1,
        "filme": "Filme Teste",
        "emissao": "2025-12-01T12:00:00+00:00",
        "assento": None,
        "assinatura": "deadbeef"
    }

    # Mock para fazer a verificação de assinatura falhar
    with patch("src.service.load_public_key") as mock_pub:
        mock_key = MagicMock()
        mock_key.verify.side_effect = ValueError("Assinatura inválida")  # força ValueError
        mock_pub.return_value = mock_key

        with pytest.raises(ValueError):
            verify_ticket_payload(ticket_falso)

# CT06b - Ticket já utilizado
def test_ticket_ja_utilizado_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key
        ticket = issue_ticket(sala)

    with patch("src.service.load_public_key") as mock_pub:
        mock_pub.return_value = MagicMock()
        mock_pub.return_value.verify.return_value = True

        # Primeiro uso do ticket passa
        assert verify_ticket_payload(ticket) is True

        # Segundo uso do mesmo ticket levanta ValueError
        with pytest.raises(ValueError):
            verify_ticket_payload(ticket)

# CT06c - Emissão com ingressos zerados
def test_ticket_ingressos_zerados_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")
    sala.filme.ingressos = 0

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        with pytest.raises(ValueError):
            issue_ticket(sala)

# CT06d - Emissão considerando idade mínima
def test_ticket_idade_minima_mock():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Adulto", "Drama", 16, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        fake_private_key = MagicMock()
        fake_private_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_private_key

        ticket = issue_ticket(sala)

    assert ticket["filme"] == "Filme Adulto"
    assert sala.filme.ingressos == 49
