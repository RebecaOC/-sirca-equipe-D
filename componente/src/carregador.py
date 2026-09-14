# -*- coding: utf-8 -*-
"""Carrega os registros brutos e devolve uma lista de dicionarios.

Este modulo e o primeiro a ser implementado, na semana 5.
Cuidado: os arquivos brutos tem sujeira. Ler nao e limpar.
"""

import csv
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRUTOS = os.path.join(RAIZ, "dados", "brutos")


def carregar_csv(caminho, encoding="utf-8", separador=","):
    """Le um arquivo csv e devolve uma lista de dicionarios.

    Atencao: o arquivo frequencia_export_sistema_antigo.csv esta em latin-1 e
    usa ponto e virgula como separador.
    """
    with open(caminho, newline="", encoding=encoding) as fh:
        return list(csv.DictReader(fh, delimiter=separador))


def normalizar_texto(valor):
    """Remove espacos sobrando e padroniza a caixa. Implemente na semana 5."""
    raise NotImplementedError("Semana 5 - implemente normalizar_texto")


def normalizar_data(valor):
    """Converte as varias formas de data encontradas para date.

    Formatos observados na base: dd/mm/aaaa, aaaa-mm-dd, dd-mm-aa, dd/mm/aa e
    textos por extenso. Decida o que fazer com o que nao converter e REGISTRE
    a decisao no relatorio de qualidade.
    """
    raise NotImplementedError("Semana 5 - implemente normalizar_data")


def normalizar_presenca(valor):
    """Reduz as marcacoes de presenca a um dominio fechado.

    Dominio alvo: presente, falta, justificada, indefinido.
    """
    raise NotImplementedError("Semana 5 - implemente normalizar_presenca")
