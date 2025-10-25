
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os, json, base64
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "state.enc"

def derive_key(password: str, salt: bytes, iterations: int = 200000) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(password.encode())

def encrypt_state(obj: dict, password: str):
    data = json.dumps(obj, ensure_ascii=False).encode()
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, data, None)
    payload = {
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ct).decode()
    }
    STATE_FILE.write_text(json.dumps(payload))
    return True

def decrypt_state(password: str):
    if not STATE_FILE.exists():
        return None
    payload = json.loads(STATE_FILE.read_text())
    salt = base64.b64decode(payload["salt"])
    nonce = base64.b64decode(payload["nonce"])
    ct = base64.b64decode(payload["ciphertext"])
    try:
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)
        pt = aesgcm.decrypt(nonce, ct, None)
        return json.loads(pt.decode())
    except Exception as e:
        raise e
