# src/crypto_keys.py
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from pathlib import Path
import getpass

def _rsa_dir() -> Path:
    # sobe de src/ para a raiz do projeto e usa data/rsa_keys
    root = Path(__file__).resolve().parents[1]
    d = root / "data" / "rsa_keys"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _private_path() -> Path:
    return _rsa_dir() / "private_key.pem"

def _public_path() -> Path:
    return _rsa_dir() / "public_key.pem"

def generate_keys():
    senha = getpass.getpass("Digite uma senha para proteger a chave privada: ").encode()

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    priv_path = _private_path()
    pub_path = _public_path()

    with open(priv_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(senha)
        ))

    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print(f"Chaves geradas com sucesso! Arquivos: {priv_path} e {pub_path}")

def load_private_key():
    priv_path = _private_path()
    if not priv_path.exists():
        raise FileNotFoundError(f"Arquivo de chave privada não encontrado: {priv_path}")
    senha = getpass.getpass("Digite a senha da chave privada: ").encode()
    with open(priv_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=senha)

def load_public_key():
    pub_path = _public_path()
    if not pub_path.exists():
        raise FileNotFoundError(f"Arquivo de chave pública não encontrado: {pub_path}")
    with open(pub_path, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def sign_payload(private_key, payload: bytes) -> bytes:
    """
    private_key: objeto retornado por load_private_key()
    payload: bytes (já serializado)
    """
    signature = private_key.sign(
        payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(public_key, payload: bytes, signature: bytes) -> bool:
    """
    public_key: objeto retornado por load_public_key()
    payload: bytes
    signature: bytes
    """
    try:
        public_key.verify(
            signature,
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
