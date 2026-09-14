# -*- coding: utf-8 -*-
"""Indice de registros por chave.

Comparar a busca em lista com a busca por chave e o experimento central da
semana 10. Nao apague a versao lenta: ela e a base da comparacao.
"""


def indexar_por_chave(registros, campo_chave):
    """Devolve um dicionario chave -> lista de registros. Semana 10."""
    raise NotImplementedError("Semana 10 - implemente indexar_por_chave")


def buscar_em_lista(registros, campo, valor):
    """Busca percorrendo item a item. Mantida de proposito para comparacao."""
    return [r for r in registros if r.get(campo) == valor]


def buscar_no_indice(indice, valor):
    """Busca usando o indice construido. Semana 10."""
    raise NotImplementedError("Semana 10 - implemente buscar_no_indice")
