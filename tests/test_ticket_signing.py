from src.crypto_keys import generate_keys, load_private_key, load_public_key, sign_payload, verify_signature
import json, getpass

def test_sign_verify(tmp_path, monkeypatch):
    # simula digitação da senha durante os testes
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": "senh@_test3")

    # redireciona o diretório de chaves para dentro do tmp_path
    import src.crypto_keys as ck
    ck.KEY_DIR = tmp_path / "rsa_keys"
    ck.PRIVATE_KEY_PATH = ck.KEY_DIR / "private_key.pem"
    ck.PUBLIC_KEY_PATH = ck.KEY_DIR / "public_key.pem"

    # gera e testa as chaves
    generate_keys()
    priv = load_private_key()
    pub = load_public_key()

    payload = json.dumps({"a":1}, sort_keys=True).encode()
    sig = sign_payload(priv, payload)
    ok = verify_signature(pub, payload, sig)
    assert ok
