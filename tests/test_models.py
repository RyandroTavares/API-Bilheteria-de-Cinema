
from src.models import Sala, Filme
def test_emitir_decrementa():
    filme = Filme(nome="X", genero="A", idade_minima=12, ingressos=2, data_saida="2025-12-31")
    sala = Sala(numero=1, filme=filme)
    t = sala.emitir_ingresso()
    assert sala.filme.ingressos==1
    assert "id" in t
