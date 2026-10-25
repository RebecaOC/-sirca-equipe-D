"""
Estruturas de dados do componente de organização e recuperação (E2.6).

- ListaEncadeada: guarda os registros na ordem em que chegaram.
- Pilha (LIFO): guarda o histórico de operações, para poder desfazer.
- Fila (FIFO): guarda os registros com problema, na ordem em que apareceram.
- IndicePorChave: tabela hash com encadeamento, para achar um registro pela chave.

Os dados ficam em nós encadeados (classe No). A única lista do Python usada
para guardar dados é o vetor de baldes da tabela hash, que funciona como um
array de tamanho fixo.
"""


class No:
    """Nó usado pela lista, pela pilha, pela fila e pelos baldes do índice."""

    def __init__(self, valor, proximo=None):
        self.valor = valor
        self.proximo = proximo


# ---------------------------------------------------------------------------
# Lista encadeada
# ---------------------------------------------------------------------------
class ListaEncadeada:
    """Lista simplesmente encadeada com ponteiros para o início e para o fim."""

    def __init__(self):
        self._inicio = None
        self._fim = None
        self._tamanho = 0

    def __len__(self):
        return self._tamanho

    def __iter__(self):
        atual = self._inicio
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def esta_vazia(self):
        return self._tamanho == 0

    def inserir_inicio(self, valor):
        """Insere no início. O(1)."""
        novo = No(valor, self._inicio)
        self._inicio = novo
        if self._fim is None:  # a lista estava vazia
            self._fim = novo
        self._tamanho += 1

    def inserir_fim(self, valor):
        """Insere no fim. O(1), por causa do ponteiro _fim."""
        novo = No(valor)
        if self._fim is None:  # a lista estava vazia
            self._inicio = novo
        else:
            self._fim.proximo = novo
        self._fim = novo
        self._tamanho += 1

    def inserir_em(self, posicao, valor):
        """Insere na posição indicada (0 = início). O(n)."""
        if posicao < 0 or posicao > self._tamanho:
            raise IndexError("posição fora da lista")
        if posicao == 0:
            self.inserir_inicio(valor)
        elif posicao == self._tamanho:
            self.inserir_fim(valor)
        else:
            anterior = self._no_na_posicao(posicao - 1)
            anterior.proximo = No(valor, anterior.proximo)
            self._tamanho += 1

    def obter(self, posicao):
        """Retorna o valor que está na posição indicada. O(n)."""
        if posicao < 0 or posicao >= self._tamanho:
            raise IndexError("posição fora da lista")
        return self._no_na_posicao(posicao).valor

    def buscar(self, condicao):
        """Busca sequencial: retorna todos os valores em que condicao(valor) é
        verdadeira, na ordem da lista. O(n)."""
        encontrados = []
        for valor in self:
            if condicao(valor):
                encontrados.append(valor)
        return encontrados

    def remover_primeiro(self, condicao):
        """Remove o primeiro valor em que condicao(valor) é verdadeira.

        Retorna (posicao, valor) do item removido, ou None se nenhum
        valor atender à condição. O(n).
        """
        anterior = None
        atual = self._inicio
        posicao = 0
        while atual is not None:
            if condicao(atual.valor):
                if anterior is None:  # removendo o primeiro nó
                    self._inicio = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                if atual is self._fim:  # removendo o último nó
                    self._fim = anterior
                self._tamanho -= 1
                return posicao, atual.valor
            anterior = atual
            atual = atual.proximo
            posicao += 1
        return None

    def _no_na_posicao(self, posicao):
        atual = self._inicio
        for _ in range(posicao):
            atual = atual.proximo
        return atual


# ---------------------------------------------------------------------------
# Pilha
# ---------------------------------------------------------------------------
class Pilha:
    """Pilha: o último a entrar é o primeiro a sair. Todas as operações são O(1)."""

    def __init__(self):
        self._topo = None
        self._tamanho = 0

    def __len__(self):
        return self._tamanho

    def esta_vazia(self):
        return self._tamanho == 0

    def empilhar(self, valor):
        self._topo = No(valor, self._topo)
        self._tamanho += 1

    def desempilhar(self):
        if self._topo is None:
            raise IndexError("pilha vazia")
        valor = self._topo.valor
        self._topo = self._topo.proximo
        self._tamanho -= 1
        return valor

    def topo(self):
        """Mostra o valor do topo sem retirá-lo."""
        if self._topo is None:
            raise IndexError("pilha vazia")
        return self._topo.valor


# ---------------------------------------------------------------------------
# Fila
# ---------------------------------------------------------------------------
class Fila:
    """Fila: o primeiro a entrar é o primeiro a sair.

    Com ponteiros para a frente e para o fim, enfileirar e desenfileirar
    são O(1).
    """

    def __init__(self):
        self._frente = None
        self._fim = None
        self._tamanho = 0

    def __len__(self):
        return self._tamanho

    def __iter__(self):
        """Percorre a fila da frente para o fim, sem retirar nada."""
        atual = self._frente
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def esta_vazia(self):
        return self._tamanho == 0

    def enfileirar(self, valor):
        novo = No(valor)
        if self._fim is None:  # a fila estava vazia
            self._frente = novo
        else:
            self._fim.proximo = novo
        self._fim = novo
        self._tamanho += 1

    def desenfileirar(self):
        if self._frente is None:
            raise IndexError("fila vazia")
        valor = self._frente.valor
        self._frente = self._frente.proximo
        if self._frente is None:  # a fila ficou vazia
            self._fim = None
        self._tamanho -= 1
        return valor

    def frente(self):
        """Mostra o valor da frente sem retirá-lo."""
        if self._frente is None:
            raise IndexError("fila vazia")
        return self._frente.valor


# ---------------------------------------------------------------------------
# Índice por chave (tabela hash)
# ---------------------------------------------------------------------------
_AUSENTE = object()  # marcador para diferenciar "chave não existe" de valor None


class IndicePorChave:
    """Tabela hash com encadeamento separado.

    Cada posição do vetor (balde) guarda uma cadeia de nós com pares
    (chave, valor). Chaves diferentes que caem na mesma posição (colisão)
    ficam na mesma cadeia. Inserir, buscar e remover custam O(1) em média.
    Quando a ocupação passa de 75%, o vetor dobra de tamanho e as chaves
    são redistribuídas.
    """

    CAPACIDADE_INICIAL = 8
    OCUPACAO_MAXIMA = 0.75

    def __init__(self, capacidade=CAPACIDADE_INICIAL):
        self._capacidade = max(1, capacidade)
        self._baldes = [None] * self._capacidade
        self._tamanho = 0

    def __len__(self):
        return self._tamanho

    def __contains__(self, chave):
        return self.contem(chave)

    def _posicao(self, chave):
        """Função hash polinomial: transforma a chave em uma posição do vetor."""
        h = 0
        for caractere in str(chave):
            h = (h * 31 + ord(caractere)) % self._capacidade
        return h

    def inserir(self, chave, valor):
        """Associa o valor à chave.

        Retorna True se a chave era nova. Se a chave já existia, substitui
        o valor e retorna False.
        """
        posicao = self._posicao(chave)
        atual = self._baldes[posicao]
        while atual is not None:
            if atual.valor[0] == chave:
                atual.valor = (chave, valor)
                return False
            atual = atual.proximo
        self._baldes[posicao] = No((chave, valor), self._baldes[posicao])
        self._tamanho += 1
        if self._tamanho / self._capacidade > self.OCUPACAO_MAXIMA:
            self._redimensionar(self._capacidade * 2)
        return True

    def buscar(self, chave, padrao=None):
        """Retorna o valor da chave, ou `padrao` se a chave não existir."""
        atual = self._baldes[self._posicao(chave)]
        while atual is not None:
            if atual.valor[0] == chave:
                return atual.valor[1]
            atual = atual.proximo
        return padrao

    def contem(self, chave):
        return self.buscar(chave, _AUSENTE) is not _AUSENTE

    def remover(self, chave):
        """Remove a chave e retorna o valor dela, ou None se ela não existir."""
        posicao = self._posicao(chave)
        anterior = None
        atual = self._baldes[posicao]
        while atual is not None:
            if atual.valor[0] == chave:
                if anterior is None:
                    self._baldes[posicao] = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                self._tamanho -= 1
                return atual.valor[1]
            anterior = atual
            atual = atual.proximo
        return None

    def chaves(self):
        """Percorre todas as chaves (sem ordem definida)."""
        for balde in self._baldes:
            atual = balde
            while atual is not None:
                yield atual.valor[0]
                atual = atual.proximo

    def _redimensionar(self, nova_capacidade):
        baldes_antigos = self._baldes
        self._capacidade = nova_capacidade
        self._baldes = [None] * nova_capacidade
        self._tamanho = 0
        for balde in baldes_antigos:
            atual = balde
            while atual is not None:
                chave, valor = atual.valor
                self.inserir(chave, valor)
                atual = atual.proximo
