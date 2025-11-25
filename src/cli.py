from datetime import datetime, timezone
from .models import Sala, Filme
from .storage import encrypt_state, decrypt_state, STATE_FILE
from .crypto_keys import generate_keys, load_public_key, verify_signature
from .utils import validar_data_iso
from .service import find_sala, add_filme_to_sala, remove_filme_from_sala, issue_ticket, filter_salas, initialize_state
from pathlib import Path
import json, getpass, os
from tabulate import tabulate
from typing import List # <-- Adicionado para corrigir o NameError

# Configuração de Arquivos
# PW_FILE removido conforme solicitação
TICKET_DIR = Path(__file__).resolve().parent.parent / "data" / "tickets"
TICKET_DIR.mkdir(exist_ok=True)

# Helper para conversão de estado (Lista de Salas -> Dict para Save)
def salas_to_dict_state(salas: List[Sala]) -> dict:
    return {"salas": [s.to_dict() for s in salas]}

# Helper para conversão de estado (Dict do Load -> Lista de Salas)
def dict_state_to_salas(data: dict) -> List[Sala]:
    if "salas" in data:
        return [Sala.from_dict(s) for s in data["salas"]]
    return initialize_state()

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
    """Carrega o estado criptografado interativamente."""
    if not STATE_FILE.exists():
        print("Arquivo de estado não encontrado. Inicializando com salas padrão.")
        return initialize_state()
        
    pwd = getpass.getpass("Senha para descriptografar estado: ")
    try:
        data_dict = decrypt_state(pwd)
        return dict_state_to_salas(data_dict)
    except Exception:
        print("Falha ao descriptografar. Modo somente leitura com estado vazio.")
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
    """Lista o estado atual das salas usando o objeto Sala."""
    rows = []
    for s in state:
        f = s.filme
        if f:
            # Formatação de data (só para exibição)
            try:
                data_br = datetime.strptime(f.data_saida, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                data_br = f.data_saida # Mantém o ISO se falhar
            rows.append([s.numero, f.nome, f.genero, f.idade_minima, f.ingressos, data_br])
        else:
            rows.append([s.numero, "-", "-", "-", "-", "-"])
    print(tabulate(rows, headers=["Sala","Filme","Gênero","Idade Min","Ingressos","Data Saída"]))

def adicionar_filme(state: List[Sala]):
    """Coleta dados e chama o serviço para adicionar o filme."""
    try:
        numero = int(input("Número da sala (1-5): ").strip())
    except ValueError:
        print("❌ Número inválido")
        return

    sala = find_sala(state, numero)
    if not sala:
        print("❌ Sala inexistente")
        return

    if sala.filme:
        if input(f"A Sala {numero} já tem o filme '{sala.filme.nome}'. Substituir? (S/N): ").lower() != "s":
            return

    nome = input("Nome do filme: ").strip()
    genero = input("Gênero: ").strip()

    # Validação da idade mínima
    while True:
        idade_str = input("Idade mínima [ou cancelar]: ").strip()
        if idade_str == "cancelar": return print("Operação cancelada.")
        if not idade_str.isdigit() or not (0 <= (idade := int(idade_str)) <= 18):
            print("❌ A idade mínima deve ser um número inteiro entre 0 (livre) e 18.")
            continue
        break

    # Validação de data (conversão de BR para ISO)
    data_iso = None
    while True:
        data_br = input("Data de saída (DD/MM/AAAA) [ou cancelar]: ").strip()
        if data_br == "cancelar": return print("Operação cancelada.")

        try:
            data_saida = datetime.strptime(data_br, "%d/%m/%Y")
            hoje = datetime.now()
            
            # Garante que a data é futura
            if data_saida.date() <= hoje.date():
                print("❌ A data de saída deve ser posterior à data de hoje.")
                continue

            data_iso = data_saida.strftime("%Y-%m-%d")
            break
        except ValueError:
            print("❌ Data inválida. Use o formato DD/MM/AAAA.")
            
    # Chama o serviço (Lógica de Negócio)
    add_filme_to_sala(sala, nome, genero, idade, data_iso)
    print(f"✅ Filme '{nome}' adicionado/atualizado na Sala {numero} com sucesso!")

def remover_filme(state: List[Sala]):
    """Coleta dados e chama o serviço para remover o filme."""
    try:
        numero = int(input("Número da sala: ").strip())
    except ValueError:
        print("❌ Número inválido.")
        return
        
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


def verificar_ticket():
    """Verifica a validade de um ticket assinado."""
    path = input("Caminho do ticket: ").strip()
    p = Path(path)
    if not p.exists():
        print("❌ Arquivo de ticket não encontrado.")
        return
        
    try:
        obj = json.loads(p.read_text())
        sig_hex = obj.pop("assinatura", None)
        
        if not sig_hex:
            print("❌ Ticket sem assinatura.")
            return

        # Converte assinatura de hex para bytes
        sig = bytes.fromhex(sig_hex) 

        pub = load_public_key()
        
        # Recria o payload EXATAMENTE como foi assinado (sort_keys=True)
        payload = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()
        
        ok = verify_signature(pub, payload, sig)
        
        print("\n=== Verificação do Ticket ===")
        print(f"ID: {obj['id']}")
        print(f"Filme: {obj['filme']}")
        print(f"Sala: {obj['sala']}")
        print("----------------------------")
        print("Assinatura válida?" , "✅ SIM" if ok else "❌ NÃO")
        print("----------------------------")

    except FileNotFoundError:
        print("❌ Arquivo de chave pública não encontrado. Impossível verificar.")
    except Exception as e:
        print(f"❌ Erro ao verificar ticket: {e}")

def filtrar(state: List[Sala]):
    """Coleta parâmetros de filtro e exibe os resultados do serviço."""
    nome = input("Filtrar por nome (parcial, vazio ignora): ").strip()
    data_de = input("Data de (YYYY-MM-DD) (vazio ignora): ").strip()
    data_ate = input("Data até (YYYY-MM-DD) (vazio ignora): ").strip()

    # Chama o serviço
    rows = filter_salas(state, nome, data_de, data_ate)
    
    if not rows:
        print("Nenhum filme encontrado com os critérios.")
        return
        
    # Formata a data para exibição (se necessário)
    display_rows = []
    for r in rows:
         try:
            data_br = datetime.strptime(r["data_saida"], "%Y-%m-%d").strftime("%d/%m/%Y")
         except ValueError:
            data_br = r["data_saida"]
         display_rows.append([r["numero"], r["nome"], data_br, r["ingressos"]])
         
    print(tabulate(display_rows, headers=["Sala","Filme","Data Saída","Ingressos"]))

def resetar(state: List[Sala]):
    """Reseta o estado, chamando o serviço e substituindo a lista de salas."""
    if input("Confirma resetar para estado inicial? (S/N): ").lower()!="s":
        return
        
    # Substitui a lista de objetos Sala
    state[:] = initialize_state() 
    print("✅ Estado resetado.")

def menu_loop():
    """Loop principal da CLI."""
    # O estado agora é uma lista de objetos Sala
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