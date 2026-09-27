[CONTRATO.md](https://github.com/user-attachments/files/32705651/CONTRATO.md)
# Contrato de Operações — Pilha e Fila (E2.6)

Este documento define a interface das estruturas de pilha e fila **antes** da
implementação, em Python, para que o grupo valide o comportamento esperado
antes de qualquer linha de código ser escrita.

Local no repositório: `componente/CONTRATO.md`
Implementação correspondente: `componente/pilha.py` e `componente/fila.py`

---

## Exceções customizadas

```python
class EstruturaVaziaException(Exception):
    """Lançada ao tentar remover ou consultar um elemento de uma estrutura vazia."""
    pass
```

---

## Pilha (desfazer / refazer)

Estrutura LIFO (último a entrar, primeiro a sair).

```python
from typing import Any


class Pilha:
    def __init__(self) -> None:
        """Inicializa a pilha vazia."""
        self._itens: list[Any] = []

    def push(self, item: Any) -> None:
        """
        Adiciona um item no topo da pilha.

        Pré-condição: item não pode ser None.
        """
        pass

    def pop(self) -> Any:
        """
        Remove e retorna o item do topo da pilha.

        Levanta EstruturaVaziaException se a pilha estiver vazia.
        """
        pass

    def peek(self) -> Any:
        """
        Retorna o item do topo sem removê-lo.

        Levanta EstruturaVaziaException se a pilha estiver vazia.
        """
        pass

    def is_empty(self) -> bool:
        """Retorna True se a pilha estiver vazia."""
        pass

    def size(self) -> int:
        """Retorna a quantidade de itens na pilha."""
        pass
```

---

## Fila (ordem de chegada com prioridades)

Estrutura que respeita ordem de chegada (FIFO), com desempate por prioridade.
Prioridade mais alta é atendida primeiro; em empate, vale a ordem de chegada.

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class ItemFila:
    prioridade: int
    ordem_chegada: int
    item: Any = field(compare=False)


class Fila:
    def __init__(self) -> None:
        """Inicializa a fila vazia."""
        self._itens: list[ItemFila] = []
        self._contador: int = 0

    def enqueue(self, item: Any, prioridade: int) -> None:
        """
        Insere um item na fila respeitando prioridade e ordem de chegada.

        Pré-condições:
        - item não pode ser None
        - prioridade não pode ser negativa (valor maior = mais prioritário)
        """
        pass

    def dequeue(self) -> Any:
        """
        Remove e retorna o próximo item da fila (maior prioridade primeiro,
        desempate por ordem de chegada).

        Levanta EstruturaVaziaException se a fila estiver vazia.
        """
        pass

    def peek(self) -> Any:
        """
        Retorna o próximo item sem removê-lo.

        Levanta EstruturaVaziaException se a fila estiver vazia.
        """
        pass

    def is_empty(self) -> bool:
        """Retorna True se a fila estiver vazia."""
        pass

    def size(self) -> int:
        """Retorna a quantidade de itens na fila."""
        pass
```

---

## Observações

- Os corpos dos métodos (`pass`) devem ser implementados por B; a assinatura e
  o comportamento descrito na docstring **não devem mudar** sem passar pelo
  grupo primeiro.
- Este contrato deve ser validado com C (regras de negócio, ex: valores
  válidos de prioridade) e com A (que vai integrar o índice por chave e medir
  desempenho em cima dessas estruturas).
- Qualquer alteração na assinatura após o início da implementação deve ser
  registrada em ata (`atas/`) e comunicada ao grupo.
- Os testes correspondentes devem ficar em `componente/testes/` (ex:
  `test_pilha.py`, `test_fila.py`), cobrindo tanto o caso normal quanto os
  casos de erro (`EstruturaVaziaException`).

