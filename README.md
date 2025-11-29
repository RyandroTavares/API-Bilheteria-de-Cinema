
# Bilheteria de Cinema - Em Desenvolvimento

Aplicação CLI (Command-Line Interface) em Python para gerenciamento de 5 salas de cinema, com:

* Persistência criptografada do estado (AES-GCM)
* Assinatura digital de tickets (RSA)
* Armazenamento seguro de credenciais (PBKDF2-HMAC + SHA-256)

## Descrição Geral

Este sistema permite gerenciar os filmes em exibição nas salas de um cinema, com possibilidade de:

* Adicionar, remover ou atualizar filmes em cada sala
* Emitir ingressos com assinatura digital
* Visualizar a situação de todas as salas
* Filtrar filmes por nome ou data de saída prevista
* Garantir integridade e segurança utilizando criptografia e assinatura de dados

Cada sala possui:

* Número da sala
* Nome do filme
* Gênero
* Idade mínima
* Quantidade de ingressos disponíveis (inicialmente 50)
* Data prevista de saída

## Funcionalidades

* Adicionar filme a uma sala
* Atualizar ou remover filmes existentes
* Emitir ingressos (com assinatura digital RSA)
* Verificar tickets emitidos
* Listar todas as salas com status completo
* Filtrar filmes por nome ou data de saída
* Persistir dados criptografados usando AES-GCM com chave derivada por PBKDF2 (SHA-256).

### Requisitos

* Python 3.13.x
* Extensões recomendadas para VS Code:
- Python
- Pylance
* Dependências Python (automáticas via `pip install -r requirements.txt`):
- cryptography>=41.0.0
- tabulate
- pytest

### Instalação
```
Dentro da pasta src onde possui no mesmo nível o arquivo requirements.txt use o comando (Isso serve para todos os demais comandos):
pip install -r requirements.txt
```

### Execução
Inicialize (gera chaves):
```
python -m src.main --init
```

Rode o CLI:
```
python -m src.main
```

### Testes
```
# Para executar todos os testes, utilize o comando abaixo:
python -m pytest

# Para executar testes específicos, use os comandos correspondentes:
python -m pytest tests/unit        # Testes unitários
python -m pytest tests/integration # Testes de integração
python -m pytest tests/system      # Testes de sistema

# Para obter mais detalhes durante a execução dos testes, adicione a opção -v (verbose). Por exemplo:
python -m pytest -v
python -m pytest test/unit -v
```
