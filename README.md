
# Bilheteria de Cinema

**Em desenvolvimento.**
Aplicação CLI em Python para gerenciar 5 salas de cinema com persistência criptografada (AES-GCM),
assinatura de tickets (RSA) e armazenamento seguro de senha (PBKDF2 + SHA-256).

## Descrição

O objetivo do programa é permitir ao usuário adicionar, remover e atualizar filmes em exibição em cada sala do cinema. O usuário pode também emitir ingressos, verificar o status de todas as salas e filtrar filmes por nome ou data de saída prevista.
Cada sala possui:

* Número da sala
* Nome do filme
* Gênero
* Idade mínima
* Quantidade de ingressos disponíveis (inicialmente 50)
* Data prevista de saída

## Funcionalidades

* Adicionar novo filme a uma sala
* Remover ou atualizar filmes existentes
* Emitir ingresso
* Visualizar status completo das salas
* Filtrar filmes por nome e data de saída
* Persistência criptografada de dados (AES-GCM)
* Armazenamento seguro de credenciais (PBKDF2 + SHA-256)

### Instalação
```
pip install -r requirements.txt
```

### Execução
Inicialize (gera chaves e senha administrativa):
```
python -m src.main --init
```

Rode o CLI:
```
python -m src.main
```

### Testes
```
pytest -q
```
