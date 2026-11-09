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

from typing import Callable, Generic, Hashable, Iterator, List, Optional, Tuple, TypeVar

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class No(Generic[T]):
    """Nó usado pela lista, pela pilha, pela fila e pelos baldes do índice."""

    __slots__ = ("valor", "proximo")

    def __init__(self, valor: T, proximo: Optional["No[T]"] = None) -> None:
        self.valor = valor
        self.proximo = proximo


# ---------------------------------------------------------------------------
# Lista encadeada
# ---------------------------------------------------------------------------
class ListaEncadeada(Generic[T]):
    """Lista simplesmente encadeada com ponteiros para o início e para o fim."""

    def __init__(self) -> None:
        self._inicio: Optional[No[T]] = None
        self._fim: Optional[No[T]] = None
        self._tamanho = 0

    def __len__(self) -> int:
        return self._tamanho

    def __iter__(self) -> Iterator[T]:
        atual = self._inicio
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def __repr__(self) -> str:
        return f"ListaEncadeada({list(self)!r})"

    def esta_vazia(self) -> bool:
        return self._tamanho == 0

    def inserir_inicio(self, valor: T) -> None:
        """Insere no início. O(1)."""
        novo = No(valor, self._inicio)
        self._inicio = novo
        if self._fim is None:  # a lista estava vazia
            self._fim = novo
        self._tamanho += 1

    def inserir_fim(self, valor: T) -> None:
        """Insere no fim. O(1), por causa do ponteiro _fim."""
        novo: No[T] = No(valor)
        if self._fim is None:  # a lista estava vazia
            self._inicio = novo
        else:
            self._fim.proximo = novo
        self._fim = novo
        self._tamanho += 1

    def inserir_em(self, posicao: int, valor: T) -> None:
        """Insere na posição indicada (0 = início). O(n)."""
        if posicao < 0 or posicao > self._tamanho:
            raise IndexError("posição fora da lista")
        if posicao == 0:
            self.inserir_inicio(valor)
        elif posicao == self._tamanho:
            self.inserir_fim(valor)
        else:
            anterior = self._no_na_posicao(posicao - 1)
            assert anterior is not None  # garantido por 0 < posicao < tamanho
            anterior.proximo = No(valor, anterior.proximo)
            self._tamanho += 1

    def obter(self, posicao: int) -> T:
        """Retorna o valor que está na posição indicada. O(n)."""
        if posicao < 0 or posicao >= self._tamanho:
            raise IndexError("posição fora da lista")
        no = self._no_na_posicao(posicao)
        assert no is not None  # garantido pela checagem de posicao acima
        return no.valor

    def buscar(self, condicao: Callable[[T], bool]) -> List[T]:
        """Busca sequencial: retorna todos os valores em que condicao(valor) é
        verdadeira, na ordem da lista. O(n)."""
        return [valor for valor in self if condicao(valor)]

    def remover_primeiro(
        self, condicao: Callable[[T], bool]
    ) -> Optional[Tuple[int, T]]:
        """Remove o primeiro valor em que condicao(valor) é verdadeira.

        Retorna (posicao, valor) do item removido, ou None se nenhum
        valor atender à condição. O(n).
        """
        anterior: Optional[No[T]] = None
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

    def _no_na_posicao(self, posicao: int) -> Optional[No[T]]:
        atual = self._inicio
        for _ in range(posicao):
            assert atual is not None
            atual = atual.proximo
        return atual


# ---------------------------------------------------------------------------
# Pilha
# ---------------------------------------------------------------------------
class Pilha(Generic[T]):
    """Pilha: o último a entrar é o primeiro a sair. Todas as operações são O(1)."""

    def __init__(self) -> None:
        self._topo: Optional[No[T]] = None
        self._tamanho = 0

    def __len__(self) -> int:
        return self._tamanho

    def __repr__(self) -> str:
        return f"Pilha(tamanho={self._tamanho})"

    def esta_vazia(self) -> bool:
        return self._tamanho == 0

    def empilhar(self, valor: T) -> None:
        self._topo = No(valor, self._topo)
        self._tamanho += 1

    def desempilhar(self) -> T:
        if self._topo is None:
            raise IndexError("pilha vazia")
        valor = self._topo.valor
        self._topo = self._topo.proximo
        self._tamanho -= 1
        return valor

    def topo(self) -> T:
        """Mostra o valor do topo sem retirá-lo."""
        if self._topo is None:
            raise IndexError("pilha vazia")
        return self._topo.valor


# ---------------------------------------------------------------------------
# Fila
# ---------------------------------------------------------------------------
class Fila(Generic[T]):
    """Fila: o primeiro a entrar é o primeiro a sair.

    Com ponteiros para a frente e para o fim, enfileirar e desenfileirar
    são O(1).
    """

    def __init__(self) -> None:
        self._frente: Optional[No[T]] = None
        self._fim: Optional[No[T]] = None
        self._tamanho = 0

    def __len__(self) -> int:
        return self._tamanho

    def __iter__(self) -> Iterator[T]:
        """Percorre a fila da frente para o fim, sem retirar nada."""
        atual = self._frente
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def __repr__(self) -> str:
        return f"Fila({list(self)!r})"

    def esta_vazia(self) -> bool:
        return self._tamanho == 0

    def enfileirar(self, valor: T) -> None:
        novo: No[T] = No(valor)
        if self._fim is None:  # a fila estava vazia
            self._frente = novo
        else:
            self._fim.proximo = novo
        self._fim = novo
        self._tamanho += 1

    def desenfileirar(self) -> T:
        if self._frente is None:
            raise IndexError("fila vazia")
        valor = self._frente.valor
        self._frente = self._frente.proximo
        if self._frente is None:  # a fila ficou vazia
            self._fim = None
        self._tamanho -= 1
        return valor

    def frente(self) -> T:
        """Mostra o valor da frente sem retirá-lo."""
        if self._frente is None:
            raise IndexError("fila vazia")
        return self._frente.valor


# ---------------------------------------------------------------------------
# Índice por chave (tabela hash)
# ---------------------------------------------------------------------------
_AUSENTE = object()  # marcador para diferenciar "chave não existe" de valor None


class IndicePorChave(Generic[K, V]):
    """Tabela hash com encadeamento separado.

    Cada posição do vetor (balde) guarda uma cadeia de nós com pares
    (chave, valor). Chaves diferentes que caem na mesma posição (colisão)
    ficam na mesma cadeia. Inserir, buscar e remover custam O(1) em média.
    Quando a ocupação passa de 75%, o vetor dobra de tamanho e as chaves
    são redistribuídas.
    """

    CAPACIDADE_INICIAL = 8
    OCUPACAO_MAXIMA = 0.75

    def __init__(self, capacidade: int = CAPACIDADE_INICIAL) -> None:
        if capacidade < 1:
            raise ValueError("capacidade inicial deve ser pelo menos 1")
        self._capacidade = capacidade
        self._baldes: List[Optional[No[Tuple[K, V]]]] = [None] * self._capacidade
        self._tamanho = 0
        # Comparações de chave feitas pela última chamada a buscar() (RF-04).
        self.comparacoes_ultima_busca = 0

    def __len__(self) -> int:
        return self._tamanho

    def __contains__(self, chave: K) -> bool:
        return self.contem(chave)

    def __repr__(self) -> str:
        return f"IndicePorChave(tamanho={self._tamanho}, capacidade={self._capacidade})"

    def _posicao(self, chave: K) -> int:
        """Função hash polinomial: transforma a chave em uma posição do vetor."""
        h = 0
        for caractere in str(chave):
            h = (h * 31 + ord(caractere)) % self._capacidade
        return h

    def inserir(self, chave: K, valor: V) -> bool:
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

    def buscar(self, chave: K, padrao: Optional[V] = None) -> Optional[V]:
        """Retorna o valor da chave, ou `padrao` se a chave não existir."""
        atual = self._baldes[self._posicao(chave)]
        comparacoes = 0
        while atual is not None:
            comparacoes += 1
            if atual.valor[0] == chave:
                self.comparacoes_ultima_busca = comparacoes
                return atual.valor[1]
            atual = atual.proximo
        self.comparacoes_ultima_busca = comparacoes
        return padrao

    def contem(self, chave: K) -> bool:
        return self.buscar(chave, _AUSENTE) is not _AUSENTE  # type: ignore[arg-type]

    def remover(self, chave: K) -> Optional[V]:
        """Remove a chave e retorna o valor dela, ou None se ela não existir."""
        posicao = self._posicao(chave)
        anterior: Optional[No[Tuple[K, V]]] = None
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

    def chaves(self) -> Iterator[K]:
        """Percorre todas as chaves (sem ordem definida)."""
        for balde in self._baldes:
            atual = balde
            while atual is not None:
                yield atual.valor[0]
                atual = atual.proximo

    def _redimensionar(self, nova_capacidade: int) -> None:
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


# ---------------------------------------------------------------------------
# Fila com prioridade (RF-03 / RN-06)
# ---------------------------------------------------------------------------
class FilaComPrioridade(Generic[T]):
    """Fila de atendimento com prioridade legal.

    Mantém duas filas FIFO: a dos prioritários e a dos demais. Quem tem
    prioridade é chamado antes de todos os não prioritários, mas continua
    atrás dos prioritários que chegaram antes. Dentro de cada grupo vale a
    ordem de chegada. Enfileirar e chamar são O(1).
    """

    def __init__(self) -> None:
        self._prioritarios: Fila[T] = Fila()
        self._comuns: Fila[T] = Fila()

    def __len__(self) -> int:
        return len(self._prioritarios) + len(self._comuns)

    def __iter__(self) -> Iterator[T]:
        """Ordem em que as pessoas seriam chamadas, sem retirar ninguém."""
        yield from self._prioritarios
        yield from self._comuns

    def esta_vazia(self) -> bool:
        return len(self) == 0

    def enfileirar(self, valor: T, prioritario: bool = False) -> None:
        if prioritario:
            self._prioritarios.enfileirar(valor)
        else:
            self._comuns.enfileirar(valor)

    def desenfileirar(self) -> T:
        if not self._prioritarios.esta_vazia():
            return self._prioritarios.desenfileirar()
        return self._comuns.desenfileirar()  # levanta IndexError se vazia

    def frente(self) -> T:
        if not self._prioritarios.esta_vazia():
            return self._prioritarios.frente()
        return self._comuns.frente()


# ---------------------------------------------------------------------------
# Coleção ordenada com busca binária (RF-05)
# ---------------------------------------------------------------------------
def ordenar_por_merge(itens: List[T], chave: Callable[[T], str]) -> List[T]:
    """Merge sort estável, O(n log n). Não usa sorted() nem list.sort()."""
    if len(itens) <= 1:
        return list(itens)
    meio = len(itens) // 2
    esquerda = ordenar_por_merge(itens[:meio], chave)
    direita = ordenar_por_merge(itens[meio:], chave)
    resultado: List[T] = []
    i = j = 0
    while i < len(esquerda) and j < len(direita):
        if chave(direita[j]) < chave(esquerda[i]):
            resultado.append(direita[j])
            j += 1
        else:  # empate: mantém a esquerda primeiro (estável)
            resultado.append(esquerda[i])
            i += 1
    resultado.extend(esquerda[i:])
    resultado.extend(direita[j:])
    return resultado


class ColecaoOrdenada(Generic[T]):
    """Coleção ordenada por uma chave de texto, com busca binária.

    Os itens ficam em um array (lista do Python usada só como vetor
    indexável, necessário para a busca binária). A coleção é ordenada antes
    da busca sempre que entrou item novo, então o resultado não depende da
    ordem de cadastro. Se vários itens têm a mesma chave, todos são devolvidos.
    """

    def __init__(self, chave: Callable[[T], str]) -> None:
        self._chave = chave
        self._itens: List[T] = []
        self._ordenada = True
        self.comparacoes_ultima_busca = 0

    def __len__(self) -> int:
        return len(self._itens)

    def __iter__(self) -> Iterator[T]:
        self._garantir_ordem()
        return iter(self._itens)

    def adicionar(self, item: T) -> None:
        self._itens.append(item)
        self._ordenada = False

    def ordenar(self) -> None:
        """Ordena agora, se houver item novo (útil para medir só a busca)."""
        self._garantir_ordem()

    def _garantir_ordem(self) -> None:
        if not self._ordenada:
            self._itens = ordenar_por_merge(self._itens, self._chave)
            self._ordenada = True

    def buscar(self, chave: str) -> List[T]:
        """Retorna todos os itens com a chave informada (lista vazia se não houver).

        Busca binária pela primeira ocorrência e depois varre os vizinhos
        iguais. O(log n + k), com k = número de correspondentes.
        """
        self._garantir_ordem()
        comparacoes = 0
        baixo, alto = 0, len(self._itens)
        while baixo < alto:  # primeira posição com chave >= procurada
            meio = (baixo + alto) // 2
            comparacoes += 1
            if self._chave(self._itens[meio]) < chave:
                baixo = meio + 1
            else:
                alto = meio
        encontrados: List[T] = []
        posicao = baixo
        while posicao < len(self._itens):
            comparacoes += 1
            if self._chave(self._itens[posicao]) != chave:
                break
            encontrados.append(self._itens[posicao])
            posicao += 1
        self.comparacoes_ultima_busca = comparacoes
        return encontrados
