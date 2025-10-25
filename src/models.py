
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
from uuid import uuid4
from datetime import datetime

@dataclass
class Filme:
    nome: str
    genero: str
    idade_minima: int
    ingressos: int
    data_saida: str  # YYYY-MM-DD

    def to_dict(self):
        return asdict(self)

@dataclass
class Sala:
    numero: int
    filme: Optional[Filme] = None

    def esta_vazia(self) -> bool:
        return self.filme is None

    def adicionar_filme(self, filme: Filme):
        self.filme = filme

    def remover_filme(self):
        self.filme = None

    def emitir_ingresso(self):
        if self.esta_vazia():
            raise ValueError("Sala vazia")
        if self.filme.ingressos <= 0:
            raise ValueError("Ingressos esgotados")
        self.filme.ingressos -= 1
        ticket = {
            "id": str(uuid4()),
            "sala": self.numero,
            "filme": self.filme.nome,
            "emissao": datetime.utcnow().isoformat() + "Z",
            "assento": None
        }
        return ticket
