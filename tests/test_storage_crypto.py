
import tempfile, os
from src.storage import encrypt_state, decrypt_state, STATE_FILE
def test_encrypt_decrypt_roundtrip(tmp_path, monkeypatch):
    pwd = "testsenha"
    state = {"salas":[{"numero":1, "filme":None}]}
    # use tmp file
    monkeypatch.setenv("PYTHONIOENCODING","utf-8")
    # point STATE_FILE to tmp
    from pathlib import Path
    import importlib
    st = importlib.import_module("src.storage")
    st.STATE_FILE = Path(tmp_path)/"state.enc"
    st.encrypt_state(state, pwd)
    loaded = st.decrypt_state(pwd)
    assert loaded==state
