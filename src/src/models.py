from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

@dataclass
class Filme:
    nome: str
    genero: str
    idade_minima: int
    ingressos: int
    data_saida: str # Formato ISO YYYY-MM-DD

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> 'Filme':
        """Cria um objeto Filme a partir de um dicionário."""
        return Filme(**data)

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
            "emissao": datetime.now(timezone.utc).isoformat(),
            "assento": None
        }
        return ticket
    
    def to_dict(self) -> dict:
        """Serializa a Sala (incluindo o Filme, se houver) para dicionário."""
        data = {"numero": self.numero, "filme": None}
        if self.filme:
            data["filme"] = self.filme.to_dict()
        return data

    @staticmethod
    def from_dict(data: dict) -> 'Sala':
        """Cria um objeto Sala a partir de um dicionário."""
        filme_data = data.get("filme")
        filme = Filme.from_dict(filme_data) if filme_data else None
        return Sala(numero=data["numero"], filme=filme)