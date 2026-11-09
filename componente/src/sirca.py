"""
Regras de negócio do SIRCA que o componente precisa cumprir (RF-01 a RF-05).

- RF-01 / RN-01 / RN-02 / RF-10: lançar presença em edição de oficina, com
  desfazer e refazer, no máximo um registro por participante por edição e
  histórico das correções.
- RF-02 / RN-03: histórico de participação de um participante, do mais recente
  para o mais antigo, vazio (sem erro) quando não há registro.
- RF-03 / RN-06: fila de atendimento da assistente social por ordem de chegada,
  com prioridade legal para idoso, gestante e pessoa com deficiência.
- RF-04: busca de participante por código pelo índice hash, com contagem de
  comparações.
- RF-05: busca de participante por nome em coleção ordenada (busca binária),
  com tempo medido.

Valor de trabalho da QA-03 (precedência entre grupos prioritários): enquanto a
coordenação não responder, idoso, gestante e pessoa com deficiência formam um
único grupo prioritário, atendido por ordem de chegada; quem pertence a mais de
um grupo ocupa uma só posição, a da sua chegada.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from time import perf_counter_ns
from typing import Callable, List, Optional, Tuple

from estruturas import (
    ColecaoOrdenada,
    FilaComPrioridade,
    IndicePorChave,
    ListaEncadeada,
    Pilha,
    ordenar_por_merge,
)

# RN-01: as três condições válidas de frequência.
PRESENTE = "presente"
AUSENTE = "ausente"
AUSENTE_JUSTIFICADO = "ausente justificado"
CONDICOES_VALIDAS = (PRESENTE, AUSENTE, AUSENTE_JUSTIFICADO)

_OP_LANCAR = "lancar"
_OP_CORRIGIR = "corrigir"


class ErroDeRegra(ValueError):
    """Lançamento recusado por violar uma regra de negócio."""


@dataclass
class Participante:
    codigo: str
    nome: str


@dataclass
class Edicao:
    codigo: str
    oficina: str
    data: date
    vinculados: "IndicePorChave[str, bool]" = field(default_factory=IndicePorChave)


@dataclass
class RegistroFrequencia:
    edicao: str
    participante: str
    condicao: str
    responsavel: str
    instante: datetime
    versao: int = 1


@dataclass
class Chegada:
    nome: str
    idoso: bool
    gestante: bool
    pessoa_com_deficiencia: bool
    ordem: int

    @property
    def prioritaria(self) -> bool:
        return self.idoso or self.gestante or self.pessoa_com_deficiencia


@dataclass
class ResultadoBusca:
    """Resultado de uma busca de participante.

    `encontrados` é vazio quando não há correspondente (não é erro).
    `tempo_ns` é o tempo medido da operação, em nanossegundos.
    """

    encontrados: List[Participante]
    comparacoes: int
    tempo_ns: int

    @property
    def tempo(self) -> str:
        """Tempo com a unidade indicada (RF-05, critério 1)."""
        if self.tempo_ns >= 1_000_000:
            return f"{self.tempo_ns / 1_000_000:.3f} ms"
        return f"{self.tempo_ns / 1_000:.3f} µs"


def _chave_ordem(registro: RegistroFrequencia, data_edicao: date) -> str:
    return f"{data_edicao.isoformat()}|{registro.instante.isoformat()}"


class Sirca:
    def __init__(self, relogio: Callable[[], datetime] = datetime.now) -> None:
        self._relogio = relogio
        self.participantes: IndicePorChave[str, Participante] = IndicePorChave()
        self._por_nome: ColecaoOrdenada[Participante] = ColecaoOrdenada(
            lambda p: p.nome.strip().casefold()
        )
        self.edicoes: IndicePorChave[str, Edicao] = IndicePorChave()
        # chave "edicao|participante" -> registro vigente
        self._vigentes: IndicePorChave[str, RegistroFrequencia] = IndicePorChave()
        # chave "edicao|participante" -> versões anteriores (RN-02)
        self._versoes: IndicePorChave[
            str, ListaEncadeada[RegistroFrequencia]
        ] = IndicePorChave()
        # código do participante -> registros vigentes dele
        self._por_participante: IndicePorChave[
            str, ListaEncadeada[RegistroFrequencia]
        ] = IndicePorChave()
        self._desfazer: Pilha[
            Tuple[str, RegistroFrequencia, Optional[RegistroFrequencia]]
        ] = Pilha()
        self._refazer: Pilha[
            Tuple[str, RegistroFrequencia, Optional[RegistroFrequencia]]
        ] = Pilha()
        self.atendimento: FilaComPrioridade[Chegada] = FilaComPrioridade()
        self._proxima_ordem = 1

    # ------------------------------------------------------------------
    # Cadastros mínimos (a carga completa é feita pelo banco, RF-06)
    # ------------------------------------------------------------------
    def cadastrar_participante(self, codigo: str, nome: str) -> Participante:
        codigo, nome = codigo.strip(), nome.strip()
        if not codigo or not nome:
            raise ErroDeRegra("código e nome do participante são obrigatórios")
        if codigo in self.participantes:
            raise ErroDeRegra(f"código de participante repetido: {codigo}")
        participante = Participante(codigo, nome)
        self.participantes.inserir(codigo, participante)
        self._por_nome.adicionar(participante)
        return participante

    def cadastrar_edicao(self, codigo: str, oficina: str, data: date) -> Edicao:
        codigo = codigo.strip()
        if not codigo or codigo in self.edicoes:
            raise ErroDeRegra(f"código de edição vazio ou repetido: {codigo!r}")
        edicao = Edicao(codigo, oficina.strip(), data)
        self.edicoes.inserir(codigo, edicao)
        return edicao

    def vincular(self, codigo_edicao: str, codigo_participante: str) -> None:
        edicao = self._edicao(codigo_edicao)
        if codigo_participante not in self.participantes:
            raise ErroDeRegra(f"participante inexistente: {codigo_participante}")
        edicao.vinculados.inserir(codigo_participante, True)

    # ------------------------------------------------------------------
    # RF-01: lançamento de frequência
    # ------------------------------------------------------------------
    def lancar_presenca(
        self, edicao: str, participante: str, condicao: str, responsavel: str
    ) -> RegistroFrequencia:
        """Grava a frequência de um participante em uma edição.

        Recusa (ErroDeRegra): condição fora de RN-01, responsável vazio (RF-10),
        edição ou participante inexistente, participante não vinculado à
        edição e registro já existente (RN-02: use corrigir_presenca).
        """
        self._validar(edicao, participante, condicao, responsavel)
        chave = f"{edicao}|{participante}"
        if chave in self._vigentes:
            raise ErroDeRegra(
                "já existe registro deste participante nesta edição; "
                "use corrigir_presenca (RN-02)"
            )
        registro = RegistroFrequencia(
            edicao, participante, condicao, responsavel.strip(), self._relogio()
        )
        self._gravar(registro, None)
        self._desfazer.empilhar((_OP_LANCAR, registro, None))
        self._refazer = Pilha()  # uma ação nova invalida o "refazer"
        return registro

    def corrigir_presenca(
        self, edicao: str, participante: str, condicao: str, responsavel: str
    ) -> RegistroFrequencia:
        """Corrige um registro existente, preservando o valor anterior (RN-02)."""
        self._validar(edicao, participante, condicao, responsavel)
        chave = f"{edicao}|{participante}"
        anterior = self._vigentes.buscar(chave)
        if anterior is None:
            raise ErroDeRegra("não há registro para corrigir; use lancar_presenca")
        novo = RegistroFrequencia(
            edicao,
            participante,
            condicao,
            responsavel.strip(),
            self._relogio(),
            anterior.versao + 1,
        )
        self._gravar(novo, anterior)
        self._desfazer.empilhar((_OP_CORRIGIR, novo, anterior))
        self._refazer = Pilha()
        return novo

    def desfazer(self) -> Optional[str]:
        """Desfaz o último lançamento ou correção. None se não houver o que desfazer."""
        if self._desfazer.esta_vazia():
            return None
        operacao, registro, anterior = self._desfazer.desempilhar()
        self._retirar(registro, anterior)
        self._refazer.empilhar((operacao, registro, anterior))
        return operacao

    def refazer(self) -> Optional[str]:
        """Refaz a última operação desfeita. None se não houver o que refazer."""
        if self._refazer.esta_vazia():
            return None
        operacao, registro, anterior = self._refazer.desempilhar()
        self._gravar(registro, anterior)
        self._desfazer.empilhar((operacao, registro, anterior))
        return operacao

    def consultar_registro(
        self, edicao: str, participante: str
    ) -> Optional[RegistroFrequencia]:
        """Registro vigente, com responsável e instante do lançamento (RF-10)."""
        return self._vigentes.buscar(f"{edicao}|{participante}")

    def versoes_anteriores(
        self, edicao: str, participante: str
    ) -> List[RegistroFrequencia]:
        """Valores anteriores preservados pelas correções, do mais antigo ao mais novo."""
        lista = self._versoes.buscar(f"{edicao}|{participante}")
        return list(lista) if lista is not None else []

    # ------------------------------------------------------------------
    # RF-02: histórico de participação
    # ------------------------------------------------------------------
    def historico_do_participante(self, codigo: str) -> List[RegistroFrequencia]:
        """Registros do participante, do mais recente para o mais antigo.

        Código inexistente ou sem frequência devolve lista vazia, sem erro.
        """
        lista = self._por_participante.buscar(codigo.strip())
        if lista is None:
            return []

        def chave(r: RegistroFrequencia) -> str:
            edicao = self.edicoes.buscar(r.edicao)
            assert edicao is not None
            return _chave_ordem(r, edicao.data)

        crescente = ordenar_por_merge(list(lista), chave)
        crescente.reverse()
        return crescente

    # ------------------------------------------------------------------
    # RF-03 / RN-06: fila de atendimento
    # ------------------------------------------------------------------
    def registrar_chegada(
        self,
        nome: str,
        idoso: bool = False,
        gestante: bool = False,
        pessoa_com_deficiencia: bool = False,
    ) -> Chegada:
        if not nome.strip():
            raise ErroDeRegra("nome de quem chegou é obrigatório")
        chegada = Chegada(
            nome.strip(), idoso, gestante, pessoa_com_deficiencia, self._proxima_ordem
        )
        self._proxima_ordem += 1
        self.atendimento.enfileirar(chegada, chegada.prioritaria)
        return chegada

    def chamar_proxima(self) -> Optional[Chegada]:
        """Chama a próxima pessoa. Fila vazia devolve None (sem erro)."""
        if self.atendimento.esta_vazia():
            return None
        return self.atendimento.desenfileirar()

    # ------------------------------------------------------------------
    # RF-04 e RF-05: busca de participante
    # ------------------------------------------------------------------
    def buscar_por_codigo(self, codigo: str) -> ResultadoBusca:
        inicio = perf_counter_ns()
        participante = self.participantes.buscar(codigo.strip())
        tempo = perf_counter_ns() - inicio
        encontrados = [participante] if participante is not None else []
        return ResultadoBusca(
            encontrados, self.participantes.comparacoes_ultima_busca, tempo
        )

    def buscar_por_nome(self, nome: str) -> ResultadoBusca:
        """Busca binária em coleção ordenada por nome (sem diferenciar maiúsculas).

        Devolve todos os participantes com aquele nome, sem escolher um.
        """
        chave = nome.strip().casefold()
        self._por_nome.ordenar()  # a ordenação não entra no tempo medido
        inicio = perf_counter_ns()
        encontrados = self._por_nome.buscar(chave)
        tempo = perf_counter_ns() - inicio
        return ResultadoBusca(encontrados, self._por_nome.comparacoes_ultima_busca, tempo)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _edicao(self, codigo: str) -> Edicao:
        edicao = self.edicoes.buscar(codigo)
        if edicao is None:
            raise ErroDeRegra(f"edição inexistente: {codigo}")
        return edicao

    def _validar(
        self, edicao: str, participante: str, condicao: str, responsavel: str
    ) -> None:
        if condicao not in CONDICOES_VALIDAS:
            raise ErroDeRegra(
                f"condição inválida: {condicao!r} (use {', '.join(CONDICOES_VALIDAS)})"
            )
        if not responsavel.strip():
            raise ErroDeRegra("identificação do responsável é obrigatória (RF-10)")
        ed = self._edicao(edicao)
        if participante not in self.participantes:
            raise ErroDeRegra(f"participante inexistente: {participante}")
        if participante not in ed.vinculados:
            raise ErroDeRegra(
                f"participante {participante} não está vinculado à edição {edicao}"
            )

    def _gravar(
        self, registro: RegistroFrequencia, anterior: Optional[RegistroFrequencia]
    ) -> None:
        chave = f"{registro.edicao}|{registro.participante}"
        lista = self._por_participante.buscar(registro.participante)
        if lista is None:
            lista = ListaEncadeada()
            self._por_participante.inserir(registro.participante, lista)
        if anterior is not None:
            lista.remover_primeiro(lambda r: r is anterior)
            versoes = self._versoes.buscar(chave)
            if versoes is None:
                versoes = ListaEncadeada()
                self._versoes.inserir(chave, versoes)
            versoes.inserir_fim(anterior)
        lista.inserir_fim(registro)
        self._vigentes.inserir(chave, registro)

    def _retirar(
        self, registro: RegistroFrequencia, anterior: Optional[RegistroFrequencia]
    ) -> None:
        chave = f"{registro.edicao}|{registro.participante}"
        lista = self._por_participante.buscar(registro.participante)
        assert lista is not None
        lista.remover_primeiro(lambda r: r is registro)
        if anterior is None:
            self._vigentes.remover(chave)
        else:
            versoes = self._versoes.buscar(chave)
            assert versoes is not None
            versoes.remover_primeiro(lambda r: r is anterior)
            lista.inserir_fim(anterior)
            self._vigentes.inserir(chave, anterior)
