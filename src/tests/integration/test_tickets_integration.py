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

# CT06b - Ticket já utilizado (integração real com JSON)
def test_ticket_ja_utilizado_integration():
    sala = Sala(numero=1)
    add_filme_to_sala(sala, "Filme Teste", "Ação", 12, "2025-12-31")

    # Apenas mock das chaves, resto é real
    with patch("src.service.load_private_key") as mock_key:
        fake_key = MagicMock()
        fake_key.sign.return_value = b"sig"
        mock_key.return_value = fake_key
        ticket = issue_ticket(sala)

    with patch("src.service.load_public_key") as mock_pub:
        mock_pub.return_value = MagicMock()
        mock_pub.return_value.verify.return_value = True

        # 1ª vez: funciona
        assert verify_ticket_payload(ticket)

        # 2ª vez: deve falhar
        with pytest.raises(ValueError):
            verify_ticket_payload(ticket)
