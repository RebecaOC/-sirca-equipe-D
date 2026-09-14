# -*- coding: utf-8 -*-
"""Ponto de entrada do componente de organizacao e recuperacao.

Execute a partir da raiz do repositorio:
    python componente/src/main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def menu():
    print()
    print("=" * 60)
    print("COMPONENTE DE ORGANIZACAO E RECUPERACAO - INSTITUTO SEMEAR")
    print("=" * 60)
    print("1 - Carregar registros brutos")
    print("2 - Conferir qualidade dos dados carregados")
    print("3 - Buscar participante")
    print("4 - Historico de um participante")
    print("5 - Medir desempenho das buscas")
    print("0 - Sair")
    return input("Opcao: ").strip()


def main():
    while True:
        opcao = menu()
        if opcao == "0":
            print("Ate logo.")
            return
        print("Opcao %s ainda nao implementada." % opcao)
        print("Implemente conforme o cronograma do Edital.")


if __name__ == "__main__":
    main()
