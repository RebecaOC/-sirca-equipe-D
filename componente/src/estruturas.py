# -*- coding: utf-8 -*-
"""Estruturas de dados do componente.

Regra da disciplina: cada estrutura e primeiro USADA, depois MODIFICADA e so
entao IMPLEMENTADA. Os esqueletos abaixo seguem essa ordem.
"""


class Pilha:
    """Ultimo a entrar, primeiro a sair. Usada para desfazer a ultima operacao."""

    def __init__(self):
        self._itens = []

    def empilhar(self, item):
        raise NotImplementedError("Semana 8 - implemente empilhar")

    def desempilhar(self):
        raise NotImplementedError("Semana 8 - implemente desempilhar")

    def vazia(self):
        return len(self._itens) == 0

    def __len__(self):
        return len(self._itens)


class Fila:
    """Primeiro a entrar, primeiro a sair. Usada para atendimento em ordem."""

    def __init__(self):
        self._itens = []

    def enfileirar(self, item):
        raise NotImplementedError("Semana 9 - implemente enfileirar")

    def desenfileirar(self):
        raise NotImplementedError("Semana 9 - implemente desenfileirar")

    def vazia(self):
        return len(self._itens) == 0

    def __len__(self):
        return len(self._itens)
