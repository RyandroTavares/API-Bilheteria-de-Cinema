# Imports padrão
import json
import getpass
from datetime import datetime
from pathlib import Path
from typing import List

# Imports internos
from .models import Sala, Filme
from .storage import encrypt_state, decrypt_state, STATE_FILE
from .crypto_keys import generate_keys, load_public_key, verify_signature
from .used_tickets import load_used_tickets, save_used_tickets
from .utils import validar_data_br, converter_data_br_para_iso
from .service import (
    find_sala,
    add_filme_to_sala,
    remove_filme_from_sala,
    issue_ticket,
    filter_salas,
    initialize_state,
)

# Import de terceiros
from tabulate import tabulate

# Configuração de Arquivos
TICKET_DIR = Path(__file__).resolve().parent.parent / "data" / "tickets"
TICKET_DIR.mkdir(exist_ok=True)

# Helper para conversão de estado (Lista de Salas -> Dict para Save)
def salas_to_dict_state(salas: List[Sala]) -> dict:
    return {"salas": [s.to_dict() for s in salas]}

# Helper para conversão de estado (Dict do Load -> Lista de Salas)
def dict_state_to_salas(data: dict) -> List[Sala]:
    try:
        if "salas" in data:
            return [Sala.from_dict(s) for s in data["salas"]]
    except Exception:
        print("⚠️ Erro ao carregar salas do estado. Inicializando padrão.")
    return initialize_state()

# Helpers de input validados
def input_numero_sala(prompt="Número da sala (1-5): ") -> int | None:
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("❌ Número inválido.")
        return None

def input_idade_minima(prompt="Idade mínima [0-18] (ou cancelar): ") -> int | None:
    while True:
        s = input(prompt).strip()
        if s.lower() == "cancelar": return None
        if s.isdigit() and 0 <= int(s) <= 18: return int(s)
        print("❌ A idade mínima deve ser entre 0 e 18.")

def input_data_futura(prompt="Data de saída (DD/MM/AAAA) [ou cancelar]: ") -> str | None:
    while True:
        s = input(prompt).strip()
        if s.lower() == "cancelar": return None
        try:
            d = datetime.strptime(s, "%d/%m/%Y")
            if d.date() <= datetime.now().date():
                print("❌ A data deve ser futura.")
                continue
            return d.strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Formato inválido. Use DD/MM/AAAA.")

def init_app():
    """Inicializa as chaves RSA e o estado inicial, se não existirem."""
    print("Inicializando aplicação...")
    
    # A lógica de senha de administrador (admin.json) foi removida.
    # O acesso agora é protegido pela senha de criptografia de estado e pela chave privada RSA.
        
    generate_keys() # Gera chaves se não existirem
    
    if not STATE_FILE.exists():
        print("Gerando arquivo de estado inicial criptografado.")
        # A senha aqui é para a criptografia do estado (AES-GCM)
        encrypt_state(salas_to_dict_state(initialize_state()), getpass.getpass("Defina senha para criptografar estado: "))
        print("Estado inicial salvo.")


def load_state_interactive() -> List[Sala]:
    if not STATE_FILE.exists():
        print("Arquivo de estado não encontrado. Inicializando com salas padrão.")
        return initialize_state()

    for _ in range(3):  # 3 tentativas
        pwd = getpass.getpass("Senha para descriptografar estado: ")
        try:
            data_dict = decrypt_state(pwd)
            return dict_state_to_salas(data_dict)
        except Exception:
            print("❌ Falha ao descriptografar, tente novamente.")
    print("Modo somente leitura com estado vazio.")
    return initialize_state()

def save_state_interactive(state: List[Sala]):
    """Salva o estado interativamente."""
    pwd = getpass.getpass("Senha para criptografar estado: ")
    data_to_save = salas_to_dict_state(state)
    try:
        encrypt_state(data_to_save, pwd)
        print("✅ Estado salvo e criptografado com sucesso.")
    except Exception as e:
        print(f"❌ Falha ao salvar estado: {e}")

def listar(state: List[Sala]):
    """Lista o estado atual das salas usando tabela."""
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
    """Coleta dados e adiciona ou atualiza um filme em uma sala."""
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

def emitir(state: List[Sala]):
    """Emite um ticket, gerando assinatura e salvando em disco."""
    try:
        numero = int(input("Número da sala: ").strip())
    except ValueError:
        print("❌ Número inválido.")
        return
        
    sala = find_sala(state, numero)

    try:
        # Lógica de Negócio (decremento de ingresso e assinatura)
        ticket = issue_ticket(sala)
        
        # Salva o ticket assinado
        path = TICKET_DIR / f"ticket_{ticket['id']}.json"
        
        # Converte a assinatura de bytes (hex string) para o formato JSON
        ticket_json_output = ticket.copy()
        ticket_json_output["assinatura"] = ticket["assinatura"]
        
        path.write_text(json.dumps(ticket_json_output, ensure_ascii=False, indent=2))
        
        print(f"🎟️ Ticket emitido para {sala.filme.nome} - Sala {numero}")
        print("Ticket gerado:", path)
        
    except (ValueError, PermissionError) as e:
        print(f"⚠️ Erro na emissão: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")


def verificar_ticket(state):
    """
    Verifica a validade de um ticket assinado (JSON), aceitando JSON em múltiplas linhas.
    Também garante anti-reutilização gravando o ID do ticket em data/used_tickets.json.
    """
    print("\n=== VERIFICAR TICKET ===")
    print("Cole o ticket JSON (finalize com uma linha vazia) ou informe caminho do arquivo:")

    # Leitura do input
    entrada = []
    while True:
        linha = input()
        if linha.strip() == "":
            break
        entrada.append(linha)

    if not entrada:
        print("Nenhum ticket informado.")
        return

    # Se for apenas um caminho de arquivo
    if len(entrada) == 1:
        p = Path(entrada[0].strip())
        if p.exists():
            try:
                ticket_text = p.read_text(encoding="utf-8")
            except Exception as e:
                print(f"❌ Falha ao ler o arquivo: {e}")
                return
        else:
            ticket_text = entrada[0]
    else:
        ticket_text = "\n".join(entrada)

    # Parse JSON
    try:
        ticket_obj = json.loads(ticket_text)
    except Exception:
        print("❌ Ticket inválido: formato JSON incorreto.")
        return

    # Campos obrigatórios
    obrigatorios = {"id", "sala", "filme", "emissao", "assinatura"}
    if not obrigatorios.issubset(ticket_obj.keys()):
        print("❌ Ticket inválido: campos obrigatórios ausentes.")
        return

    sig_hex = ticket_obj.pop("assinatura", None)
    if not sig_hex:
        print("❌ Ticket sem assinatura. INVÁLIDO.")
        return

    # Recria o payload EXATAMENTE como foi assinado (sort_keys=True)
    try:
        payload = json.dumps(ticket_obj, sort_keys=True, ensure_ascii=False).encode()
    except Exception as e:
        print(f"❌ Erro ao serializar payload para verificação: {e}")
        return

    # Converte assinatura para bytes
    try:
        sig = bytes.fromhex(sig_hex)
    except Exception:
        print("❌ Assinatura em formato inválido.")
        return

    # Carrega chave pública e verifica a assinatura
    try:
        pub = load_public_key()
    except FileNotFoundError:
        print("❌ Arquivo de chave pública não encontrado. Impossível verificar.")
        return
    except Exception as e:
        print(f"❌ Erro ao carregar chave pública: {e}")
        return

    ok = False
    try:
        ok = verify_signature(pub, payload, sig)
    except Exception:
        ok = False

    if not ok:
        print("❌ Assinatura inválida — ticket falsificado ou corrompido.")
        return

    # Controle anti-reutilização (arquivo de usados)
    used = load_used_tickets()  # set de IDs
    ticket_id = ticket_obj.get("id")
    if ticket_id in used:
        print("❌ Ticket já foi utilizado anteriormente! Acesso NEGADO.")
        return

    # Marca como usado e salva
    used.add(ticket_id)
    save_used_tickets(used)

    # Exibição e sucesso
    print("\n=== Ticket VÁLIDO ===")
    print(f"ID: {ticket_obj.get('id')}")
    print(f"Filme: {ticket_obj.get('filme')}")
    print(f"Sala: {ticket_obj.get('sala')}")
    print("Assinatura válida: ✅")
    print("Ticket agora registrado como utilizado (não pode ser reaproveitado).")
    print()


def filtrar(state):
    print("\n=== FILTRAR FILMES ===")
    nome = input("Nome parcial do filme (ou vazio): ").strip()

    # LOOP PARA DATA "DE"
    while True:
        data_de_br = input("Data de (DD/MM/AAAA) [ou cancelar]: ").strip()

        if data_de_br.lower() == "cancelar":
            print("Operação cancelada.")
            return

        if data_de_br == "":
            data_de_iso = ""
            break

        if not validar_data_br(data_de_br):
            print("❌ Data 'De' inválida. Use DD/MM/AAAA.")
            continue

        data_de_iso = converter_data_br_para_iso(data_de_br)
        break

    # LOOP PARA DATA "ATÉ"
    while True:
        data_ate_br = input("Data até (DD/MM/AAAA) [ou cancelar]: ").strip()

        if data_ate_br.lower() == "cancelar":
            print("Operação cancelada.")
            return

        if data_ate_br == "":
            data_ate_iso = ""
            break

        if not validar_data_br(data_ate_br):
            print("❌ Data 'Até' inválida. Use DD/MM/AAAA.")
            continue

        data_ate_iso = converter_data_br_para_iso(data_ate_br)
        break

    # -------------------------------
    # CHAMADA DO FILTRO
    # -------------------------------
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
    for r in resultados:
        print(f"Sala {r['numero']} | {r['nome']} | Saída: {r['data_saida']} | Ingressos: {r['ingressos']}")
    print()

def resetar(state: List[Sala]):
    """Reseta o estado, chamando o serviço e substituindo a lista de salas."""
    if input("Confirma resetar para estado inicial? (S/N): ").lower()!="s":
        return
        
    # Substitui a lista de objetos Sala
    state[:] = initialize_state() 
    print("✅ Estado resetado.")

def menu_loop():
    """Loop principal da CLI."""
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