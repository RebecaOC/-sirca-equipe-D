# -*- coding: utf-8 -*-
"""Verificador de ambiente do Projeto Integrador 2026/2.

Execute a partir da raiz do repositório:
    python ambiente/verificar_ambiente.py
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OK, FALHA = "[ OK ]", "[FALHA]"
problemas = []


def verifica(descricao, condicao, dica=""):
    print("%s %s" % (OK if condicao else FALHA, descricao))
    if not condicao:
        problemas.append((descricao, dica))
    return condicao


print("=" * 72)
print("VERIFICACAO DO AMBIENTE - PROJETO INTEGRADOR 2026/2")
print("=" * 72)

verifica("Python 3.11 ou superior (encontrado %d.%d)" % sys.version_info[:2],
         sys.version_info >= (3, 11),
         "Instale o Python 3.11 ou superior e recrie o ambiente virtual.")

verifica("Ambiente virtual ativado",
         hasattr(sys, "real_prefix") or sys.base_prefix != sys.prefix,
         "Ative o ambiente com .venv\\Scripts\\activate (Windows) ou source .venv/bin/activate.")

for pacote in ["openpyxl", "pandas", "pytest"]:
    try:
        __import__(pacote)
        achou = True
    except ImportError:
        achou = False
    verifica("Biblioteca %s instalada" % pacote, achou,
             "Rode: pip install -r requirements.txt")

try:
    import psycopg2  # noqa: F401
    tem_pg = True
except ImportError:
    tem_pg = False
verifica("Biblioteca psycopg2 instalada", tem_pg, "Rode: pip install -r requirements.txt")

pastas = ["dados/brutos", "banco", "componente/src", "componente/testes", "documentos"]
for p in pastas:
    verifica("Pasta %s existe" % p, os.path.isdir(os.path.join(RAIZ, p)),
             "Nao altere a estrutura de pastas do repositorio.")

brutos = os.path.join(RAIZ, "dados", "brutos")
arquivos = sorted(os.listdir(brutos)) if os.path.isdir(brutos) else []
verifica("Base bruta presente (%d arquivo(s))" % len(arquivos), len(arquivos) >= 3,
         "Copie os arquivos da pasta 08_base_de_dados_bruta do material inicial.")

if tem_pg:
    try:
        import psycopg2
        conexao = psycopg2.connect(host="localhost", port=5432, dbname="semear",
                                   user="semear", password="semear", connect_timeout=3)
        conexao.close()
        conectou = True
    except Exception:
        conectou = False
    verifica("Conexao com o PostgreSQL (localhost:5432/semear)", conectou,
             "Suba o banco com docker compose up -d ou ajuste as credenciais no seu ambiente.")

print("=" * 72)
if problemas:
    print("PENDENCIAS ENCONTRADAS: %d" % len(problemas))
    for d, dica in problemas:
        print(" - %s\n   -> %s" % (d, dica))
    sys.exit(1)
print("AMBIENTE PRONTO. Bom trabalho.")
