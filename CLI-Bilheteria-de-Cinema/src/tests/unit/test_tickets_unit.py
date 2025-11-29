import pytest
from unittest.mock import MagicMock, patch
from src import used_tickets
from src.models import Sala
from src.service import add_filme_to_sala, issue_ticket, verify_ticket_payload

# FIXTURE: limpa arquivo real após cada teste
@pytest.fixture(autouse=True)
def clear_used_tickets_file_after():
    yield
    if used_tickets.USED_TICKETS_FILE.exists():
        used_tickets.USED_TICKETS_FILE.write_text("[]", encoding="utf-8")

# CT06 - Ticket válido
def test_ticket_valido_unit():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")

    # Mock da assinatura
    with patch("src.service.load_private_key") as mock_key:
        fake_key = MagicMock()
        fake_key.sign.return_value = b"fake_signature"
        mock_key.return_value = fake_key
        ticket = issue_ticket(sala)

    # Mock da verificação
    with patch("src.service.load_public_key") as mock_pub:
        mock_pub.return_value = MagicMock()
        mock_pub.return_value.verify.return_value = True
        assert verify_ticket_payload(ticket) is True
        assert sala.filme.ingressos == 49

# CT06a - Ticket inválido (assinatura falsa)
def test_ticket_invalido_unit():
    ticket_falso = {
        "id": "abc",
        "sala": 1,
        "filme": "Filme",
        "emissao": "2025-12-01T12:00:00+00:00",
        "assento": None,
        "assinatura": "zzzz"
    }

    with patch("src.service.load_public_key") as mock_pub:
        key = MagicMock()
        key.verify.side_effect = ValueError("Assinatura inválida")
        mock_pub.return_value = key

        with pytest.raises(ValueError):
            verify_ticket_payload(ticket_falso)

# CT06c - Emissão com ingressos zerados
def test_ticket_ingressos_zerados_unit():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme", "Ação", 12, "2025-12-31")
    sala.filme.ingressos = 0

    with patch("src.service.load_private_key") as mock_key:
        fake_key = MagicMock()
        fake_key.sign.return_value = b"sig"
        mock_key.return_value = fake_key

        with pytest.raises(ValueError):
            issue_ticket(sala)

# CT06d - Idade mínima (não há verificação real, então apenas check)
def test_ticket_idade_minima_unit():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Adulto", "Drama", 16, "2025-12-31")

    with patch("src.service.load_private_key") as mock_key:
        k = MagicMock()
        k.sign.return_value = b"x"
        mock_key.return_value = k
        ticket = issue_ticket(sala)

    assert ticket["filme"] == "Filme Adulto"
    assert sala.filme.ingressos == 49
