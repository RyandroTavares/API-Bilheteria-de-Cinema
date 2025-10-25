
from src.crypto_keys import generate_keys, load_private_key, load_public_key, sign_payload, verify_signature
import json
def test_sign_verify(tmp_path, monkeypatch):
    generate_keys()
    priv = load_private_key()
    pub = load_public_key()
    payload = json.dumps({"a":1}, sort_keys=True).encode()
    sig = sign_payload(priv, payload)
    ok = verify_signature(pub, payload, sig)
    assert ok
