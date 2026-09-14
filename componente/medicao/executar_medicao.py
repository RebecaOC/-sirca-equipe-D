# -*- coding: utf-8 -*-
"""Roteiro da medicao experimental — semanas 11 e 13.

Preencha as chamadas e gere a tabela que vai para o Relatorio de Comparacao
Experimental de Desempenho.

    python componente/medicao/executar_medicao.py
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src"))

from instrumentacao import medir  # noqa: E402

VOLUMES = [100, 500, 1000, 5000, 10000, 50000]


def main():
    print("volume;algoritmo;media_ms;mediana_ms;desvio_ms")
    for n in VOLUMES:
        dados = list(range(n))
        alvo = n - 1  # pior caso da busca linear
        # TODO: descomente quando busca_linear e busca_binaria estiverem implementadas
        # import busca
        # r1 = medir(busca.busca_linear, dados, alvo)
        # r2 = medir(busca.busca_binaria, dados, alvo)
        # print("%d;linear;%s;%s;%s" % (n, r1["media_ms"], r1["mediana_ms"], r1["desvio_ms"]))
        # print("%d;binaria;%s;%s;%s" % (n, r2["media_ms"], r2["mediana_ms"], r2["desvio_ms"]))
        print("%d;TODO;;;" % n)

    print()
    print("Declare no relatorio: processador, memoria, sistema operacional e")
    print("versao do Python usados nesta medicao.")


if __name__ == "__main__":
    main()
