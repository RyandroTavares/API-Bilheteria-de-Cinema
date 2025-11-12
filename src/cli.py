
from datetime import datetime
from .models import Sala, Filme
from .storage import encrypt_state, decrypt_state, STATE_FILE
from .crypto_keys import generate_keys, load_private_key, load_public_key, sign_payload, verify_signature
from .auth import gerar_salt, hash_password, verify_password
from .utils import validar_data_iso
from pathlib import Path
import json, getpass, os
from tabulate import tabulate

STATE_DEFAULT = {"salas": [{"numero": i+1, "filme": None} for i in range(5)]}
PW_FILE = Path(__file__).resolve().parent.parent / "data" / "admin.json"

def init_app():
    if not PW_FILE.exists():
        print("Inicializando aplicação...")
        pwd = getpass.getpass("Defina uma senha administrativa: ")
        salt = gerar_salt()
        h = hash_password(pwd, salt)
        PW_FILE.write_bytes(json.dumps({
            "salt": salt.hex(),
            "hash": h.hex()
        }).encode())
    generate_keys()
    if not STATE_FILE.exists():
        encrypt_state(STATE_DEFAULT, getpass.getpass("Defina senha para criptografar estado (pode ser a mesma): "))

def load_state_interactive():
    if not STATE_FILE.exists():
        return STATE_DEFAULT
    pwd = getpass.getpass("Senha para descriptografar estado: ")
    try:
        return decrypt_state(pwd)
    except Exception:
        print("Falha ao descriptografar. Modo somente leitura com estado vazio.")
        return STATE_DEFAULT

def save_state_interactive(state):
    pwd = getpass.getpass("Senha para criptografar estado: ")
    encrypt_state(state, pwd)

def listar(state):
    rows = []
    for s in state["salas"]:
        f = s["filme"]
        if f:
            try:
                data_br = datetime.strptime(f["data_saida"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                data_br = f["data_saida"]
            rows.append([s["numero"], f["nome"], f["genero"], f["idade_minima"], f["ingressos"], data_br])
            
        else:
            rows.append([s["numero"], "-", "-", "-", "-", "-"])
    print(tabulate(rows, headers=["Sala","Filme","Gênero","Idade Min","Ingressos","Data Saída"]))

def encontrar_sala(state, numero):
    for s in state["salas"]:
        if s["numero"]==numero:
            return s
    return None

def adicionar_filme(state):
    try:
        numero = int(input("Número da sala (1-5): ").strip())
    except:
        print("Número inválido")
        return

    sala = encontrar_sala(state, numero)
    if not sala:
        print("Sala inexistente")
        return

    if sala["filme"]:
        if input("Já há filme. Substituir? (S/N): ").lower() != "s":
            return

    nome = input("Nome do filme: ").strip()
    genero = input("Gênero: ").strip()

    # Loop de validação da idade mínima
    while True:
        idade_str = input("Idade mínima [ou cancelar]: ").strip()

        # Cancelar
        if idade_str == "cancelar":
            print("Operação cancelada.")
            return

        # Verificar se é um número inteiro
        if not idade_str.isdigit():
            print("❌ A idade mínima deve ser um número inteiro. Tente novamente.")
            continue

        idade = int(idade_str)

        # Validar intervalo razoável
        if idade < 1:
            print("❌ A idade mínima deve ser 0 para livre ou superior.")
            continue

        # Valor aceito → sair do loop
        break


    # Loop de validação de data com formato brasileiro
    while True:
        data_br = input("Data de saída (DD/MM/AAAA) [ou cancelar]: ").strip()
        if data_br == "cancelar":
            print("Operação cancelada.")
            return

        try:
            # Converter do formato brasileiro para datetime
            data_saida = datetime.strptime(data_br, "%d/%m/%Y")

            # Validar se é uma data futura
            hoje = datetime.now()
            if data_saida.date() <= hoje.date():
                print("❌ A data de saída deve ser posterior à data de hoje.")
                continue

            # Converter para formato ISO antes de salvar
            data_iso = data_saida.strftime("%Y-%m-%d")
            break

        except ValueError:
            print("❌ Data inválida. Use o formato DD/MM/AAAA.")

    filme = {
        "nome": nome,
        "genero": genero,
        "idade_minima": idade,
        "ingressos": 50,
        "data_saida": data_iso  # Salva no formato ISO
    }

    sala["filme"] = filme
    print(f"✅ Filme '{nome}' adicionado/atualizado com sucesso!")

def remover_filme(state):
    numero = int(input("Número da sala: ").strip())
    sala = encontrar_sala(state, numero)
    if not sala or not sala["filme"]:
        print("Sala vazia ou inexistente")
        return
    sala["filme"] = None
    print("Filme removido.")

def emitir(state):
    numero = int(input("Número da sala: ").strip())
    sala = encontrar_sala(state, numero)
    if not sala or not sala["filme"]:
        print("Sala vazia ou inexistente")
        return
    if sala["filme"]["ingressos"]<=0:
        print("Ingressos esgotados")
        return
    # decrementar
    sala["filme"]["ingressos"] -= 1
    ticket = {
        "id": __import__("uuid").uuid4().hex,
        "sala": numero,
        "filme": sala["filme"]["nome"],
        "emissao": __import__("datetime").datetime.utcnow().isoformat()+"Z",
        "assento": None
    }
    # sign
    priv = load_private_key()
    import json
    payload = json.dumps(ticket, sort_keys=True, ensure_ascii=False).encode()
    sig = sign_payload(priv, payload)
    ticket["assinatura"] = sig
    path = Path(__file__).resolve().parent.parent / "data" / f"ticket_{ticket['id']}.json"
    path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2))
    print("Ticket gerado:", path)

def verificar_ticket():
    path = input("Caminho do ticket: ").strip()
    p = Path(path)
    if not p.exists():
        print("Arquivo não encontrado")
        return
    obj = json.loads(p.read_text())
    sig = obj.pop("assinatura", None)
    pub = load_public_key()
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()
    ok = verify_signature(pub, payload, sig)
    print("Assinatura válida?" , ok)

def filtrar(state):
    nome = input("Filtrar por nome (parcial, vazio ignora): ").strip().lower()
    data_de = input("Data de (YYYY-MM-DD) (vazio ignora): ").strip()
    data_ate = input("Data até (YYYY-MM-DD) (vazio ignora): ").strip()
    rows=[]
    for s in state["salas"]:
        f = s["filme"]
        if not f:
            continue
        if nome and nome not in f["nome"].lower():
            continue
        if data_de and f["data_saida"] < data_de:
            continue
        if data_ate and f["data_saida"] > data_ate:
            continue
        rows.append([s["numero"], f["nome"], f["data_saida"], f["ingressos"]])
    print(tabulate(rows, headers=["Sala","Filme","Data Saída","Ingressos"]))

def resetar(state):
    if input("Confirma resetar para estado inicial? (S/N): ").lower()!="s":
        return
    state["salas"] = [{"numero": i+1, "filme": None} for i in range(5)]
    print("Estado resetado.")

def menu_loop():
    state = load_state_interactive()
    while True:
        print("\n== Bilheteria ==")
        print("1 Listar salas")
        print("2 Adicionar/Atualizar filme")
        print("3 Remover filme")
        print("4 Emitir ingresso")
        print("5 Filtrar")
        print("6 Verificar ticket")
        print("7 Salvar estado")
        print("8 Resetar estado")
        print("0 Sair")
        op = input("Opção: ").strip()
        if op=="1":
            listar(state)
        elif op=="2":
            adicionar_filme(state)
        elif op=="3":
            remover_filme(state)
        elif op=="4":
            emitir(state)
        elif op=="5":
            filtrar(state)
        elif op=="6":
            verificar_ticket()
        elif op=="7":
            save_state_interactive(state)
        elif op=="8":
            resetar(state)
        elif op=="0":
            break
        else:
            print("Opção inválida.")
