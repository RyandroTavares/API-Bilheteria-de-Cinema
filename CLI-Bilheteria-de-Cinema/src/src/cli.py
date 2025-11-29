from typing import List
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
from getpass import getpass
import json

from .models import Sala
from .service import (
    find_sala, add_filme_to_sala, remove_filme_from_sala,
    issue_ticket, filter_salas, initialize_state
)
from .storage import encrypt_state, decrypt_state, STATE_FILE
from .crypto_keys import generate_keys, load_public_key, verify_signature
from .used_tickets import load_used_tickets, save_used_tickets
from .utils import (
    salas_to_dict_state, dict_state_to_salas,
    input_numero_sala, input_idade_minima, input_data_futura,
    validar_data_br, converter_data_br_para_iso, converter_data_iso_para_br
)

# Configuração de tickets
TICKET_DIR = Path(__file__).resolve().parent.parent / "data" / "tickets"
TICKET_DIR.mkdir(exist_ok=True)

def get_filme(sala):
    return sala.filme if hasattr(sala, "filme") else sala["filme"]

# CRUD de Filmes
def listar(state: List[Sala]):
    rows = []
    for s in state:
        f = s.filme
        if f:
            try:
                data_br = datetime.strptime(f.data_saida, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                data_br = f.data_saida
            rows.append([s.numero, f.nome, f.genero, f.idade_minima, f.ingressos, data_br])
        else:
            rows.append([s.numero, "-", "-", "-", "-", "-"])
    print(tabulate(rows, headers=["Sala","Filme","Gênero","Idade Min","Ingressos","Data Saída"]))

def adicionar_filme(state: List[Sala]):
    numero = input_numero_sala()
    if numero is None: return

    sala = find_sala(state, numero)
    if not sala:
        print("❌ Sala inexistente")
        return

    if sala.filme:
        if input(f"A Sala {numero} já tem o filme '{sala.filme.nome}'. Substituir? (S/N): ").lower() != "s":
            return

    nome = input("Nome do filme: ").strip()
    genero = input("Gênero: ").strip()
    idade = input_idade_minima()
    if idade is None:
        print("Operação cancelada.")
        return

    data_iso = input_data_futura()
    if data_iso is None:
        print("Operação cancelada.")
        return

    add_filme_to_sala(sala, nome, genero, idade, data_iso)
    print(f"✅ Filme '{nome}' adicionado/atualizado na Sala {numero} com sucesso!")

def remover_filme(state: List[Sala]):
    numero = input_numero_sala()
    if numero is None: return

    sala = find_sala(state, numero)
    if not sala or sala.esta_vazia():
        print("❌ Sala vazia ou inexistente.")
        return

    remove_filme_from_sala(sala)
    print(f"✅ Filme removido da Sala {numero}.")

# Tickets
def emitir(state: List[Sala]):
    try:
        numero = int(input("Número da sala: ").strip())
    except ValueError:
        print("❌ Número inválido.")
        return

    sala = find_sala(state, numero)
    if not sala or sala.esta_vazia():
        print("❌ Sala vazia ou inexistente.")
        return

    try:
        ticket = issue_ticket(sala)
        path = TICKET_DIR / f"ticket_{ticket['id']}.json"
        ticket_json_output = ticket.copy()
        ticket_json_output["assinatura"] = ticket["assinatura"]
        path.write_text(json.dumps(ticket_json_output, ensure_ascii=False, indent=2))
        print(f"🎟️ Ticket emitido para {sala.filme.nome} - Sala {numero}")
        print("Ticket gerado:", path)
    except Exception as e:
        print(f"❌ Erro ao emitir ticket: {e}")

def verificar_ticket(state):
    print("\n=== VERIFICAR TICKET ===")
    print("Cole o ticket JSON (finalize com uma linha vazia) ou informe caminho do arquivo:")
    entrada = []
    while True:
        linha = input()
        if linha.strip() == "": break
        entrada.append(linha)
    if not entrada:
        print("Nenhum ticket informado.")
        return

    if len(entrada) == 1 and Path(entrada[0].strip()).exists():
        try:
            ticket_text = Path(entrada[0].strip()).read_text(encoding="utf-8")
        except Exception as e:
            print(f"❌ Falha ao ler o arquivo: {e}")
            return
    else:
        ticket_text = "\n".join(entrada)

    try:
        ticket_obj = json.loads(ticket_text)
    except Exception:
        print("❌ Ticket inválido: formato JSON incorreto.")
        return

    obrigatorios = {"id", "sala", "filme", "emissao", "assinatura"}
    if not obrigatorios.issubset(ticket_obj.keys()):
        print("❌ Ticket inválido: campos obrigatórios ausentes.")
        return

    sig_hex = ticket_obj.pop("assinatura", None)
    if not sig_hex:
        print("❌ Ticket sem assinatura. INVÁLIDO.")
        return

    try:
        payload = json.dumps(ticket_obj, sort_keys=True, ensure_ascii=False).encode()
        sig = bytes.fromhex(sig_hex)
        pub = load_public_key()
        ok = verify_signature(pub, payload, sig)
    except Exception:
        print("❌ Falha na verificação da assinatura.")
        return

    if not ok:
        print("❌ Assinatura inválida — ticket falsificado ou corrompido.")
        return

    used = load_used_tickets()
    ticket_id = ticket_obj.get("id")
    if ticket_id in used:
        print("❌ Ticket já foi utilizado anteriormente! Acesso NEGADO.")
        return

    used.add(ticket_id)
    save_used_tickets(used)

    print("\n=== Ticket VÁLIDO ===")
    print(f"ID: {ticket_obj.get('id')}")
    print(f"Filme: {ticket_obj.get('filme')}")
    print(f"Sala: {ticket_obj.get('sala')}")
    print("Assinatura válida: ✅")
    print("Ticket agora registrado como utilizado (não pode ser reaproveitado).")
    print()

# Filtrar filmes
def filtrar(state):
    print("\n=== FILTRAR FILMES ===")
    nome = input("Nome parcial do filme (or vazio): ").strip()

    while True:
        data_de_br = input("Data de (DD/MM/AAAA) [ou cancelar]: ").strip()
        if data_de_br.lower() == "cancelar": return
        if data_de_br == "":
            data_de_iso = ""
            break
        if not validar_data_br(data_de_br):
            print("❌ Data 'De' inválida. Use DD/MM/AAAA.")
            continue
        data_de_iso = converter_data_br_para_iso(data_de_br)
        break

    while True:
        data_ate_br = input("Data até (DD/MM/AAAA) [ou cancelar]: ").strip()
        if data_ate_br.lower() == "cancelar": return
        if data_ate_br == "":
            data_ate_iso = ""
            break
        if not validar_data_br(data_ate_br):
            print("❌ Data 'Até' inválida. Use DD/MM/AAAA.")
            continue
        data_ate_iso = converter_data_br_para_iso(data_ate_br)
        break

    resultados = filter_salas(
        state,
        nome_parcial=nome,
        data_de=data_de_iso,
        data_ate=data_ate_iso
    )

    if not resultados:
        print("\nNenhum filme encontrado com esses critérios.\n")
        return

    print("\n--- RESULTADOS ---")
    for sala in resultados:
        filme = sala.filme
        print(
            f"Sala: {sala.numero} | Filme: {filme.nome} | Saída: {converter_data_iso_para_br(filme.data_saida)} | "
            f"Ingressos: {filme.ingressos}"
        )

    print()

# Reset de estado
def resetar(state: List[Sala]):
    if input("Confirma resetar para estado inicial? (S/N): ").lower() != "s": return
    state[:] = initialize_state()
    print("✅ Estado resetado.")

# Load / Save interativo
def load_state_interactive() -> List[Sala]:
    if not STATE_FILE.exists():
        print("Arquivo de estado não encontrado. Inicializando com salas padrão.")
        return initialize_state()

    for _ in range(3):
        pwd = getpass("Senha para descriptografar estado: ")
        try:
            data_dict = decrypt_state(pwd)
            return dict_state_to_salas(data_dict)
        except Exception:
            print("❌ Falha ao descriptografar, tente novamente.")
    print("⚠️ Modo somente leitura com estado vazio.")
    return initialize_state()

def save_state_interactive(state: List[Sala]):
    pwd = getpass("Senha para criptografar estado: ")
    data_to_save = salas_to_dict_state(state)
    try:
        encrypt_state(data_to_save, pwd)
        print("✅ Estado salvo e criptografado com sucesso.")
    except Exception as e:
        print(f"❌ Falha ao salvar estado: {e}")


# Inicialização
def init_app():
    print("Inicializando aplicação...")
    generate_keys()
    if not STATE_FILE.exists():
        print("Gerando arquivo de estado inicial criptografado.")
        encrypt_state(salas_to_dict_state(initialize_state()), getpass("Defina senha para criptografar estado: "))
        print("✅ Estado inicial salvo.")

# Menu principal
def menu_loop():
    state = load_state_interactive()
    opcoes = {
        "1": listar,
        "2": adicionar_filme,
        "3": remover_filme,
        "4": emitir,
        "5": filtrar,
        "6": verificar_ticket,
        "7": save_state_interactive,
        "8": resetar,
    }

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

        if op == "0":
            break
        elif op in opcoes:
            opcoes[op](state)
        else:
            print("Opção inválida.")
