import argparse
from .cli import init_app, menu_loop
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="Inicializar app (gerar chaves e senha)")
    args = parser.parse_args()
    if args.init:
        init_app()
        return
    menu_loop()

if __name__=="__main__":
    main()
