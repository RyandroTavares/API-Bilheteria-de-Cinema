
# Bilheteria de Cinema

Aplicação CLI em Python para gerenciar 5 salas de cinema com persistência criptografada (AES-GCM),
assinatura de tickets (RSA) e armazenamento seguro de senha (PBKDF2 + SHA-256).

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
