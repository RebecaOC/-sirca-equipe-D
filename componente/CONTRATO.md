# Contrato de Operações — Pilha e Fila 

```python
class EstruturaVaziaException(Exception):
    pass
```

```python
from typing import Any


class Pilha:
    def __init__(self) -> None:
        self._itens: list[Any] = []

    def push(self, item: Any) -> None:
        pass

    def pop(self) -> Any:
        pass

    def peek(self) -> Any:
        pass

    def is_empty(self) -> bool:
        pass

    def size(self) -> int:
        pass
```

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
        self._itens: list[ItemFila] = []
        self._contador: int = 0

    def enqueue(self, item: Any, prioridade: int) -> None:
        pass

    def dequeue(self) -> Any:
        pass

    def peek(self) -> Any:
        pass

    def is_empty(self) -> bool:
        pass

    def size(self) -> int:
        pass
```


