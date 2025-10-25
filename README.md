
# Bilheteria de Cinema

Aplicação CLI em Python para gerenciar 5 salas de cinema com persistência criptografada (AES-GCM),
assinatura de tickets (RSA) e armazenamento seguro de senha (PBKDF2 + SHA-256).

## Descrição

O objetivo do programa é permitir ao usuário adicionar, remover e atualizar filmes em exibição em cada sala do cinema.
Cada sala possui:

* Número da sala
* Nome do filme
* Gênero
* Idade mínima
* Quantidade de ingressos disponíveis (inicialmente 50)
* Data prevista de saída

O usuário pode também emitir ingressos (com assinatura digital RSA), verificar o status de todas as salas e filtrar filmes por nome ou data de saída prevista.

### Instalação
```bash
pip install -r requirements.txt
```

### Execução
Inicialize (gera chaves e senha administrativa):
```bash
python -m src.main --init
```

Rode o CLI:
```bash
python -m src.main
```

### Testes
```bash
pytest -q
```
