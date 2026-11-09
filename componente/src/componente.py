"""
Componente de organização e recuperação de registros (E2.6).

As regras do projeto (RF-01 a RF-05) estão em sirca.py; este arquivo traz a
linha de comando e o organizador genérico de registros CSV.

Junta as quatro estruturas de estruturas.py:
- ListaEncadeada -> todos os registros válidos, na ordem de chegada;
- IndicePorChave -> acesso direto a um registro pela chave;
- Fila           -> registros com problema, para a equipe revisar na ordem
                    em que apareceram;
- Pilha          -> histórico de operações, para desfazer a última.

Cada registro é um dicionário {campo: valor}, como uma linha de planilha.

Uso pela linha de comando: veja USO mais abaixo (comandos codigo, nome, demo, csv).
"""

import csv
import io
import sys
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

from estruturas import Fila, IndicePorChave, ListaEncadeada, Pilha
from sirca import ErroDeRegra, ResultadoBusca, Sirca

Registro = Dict[str, Any]

# Nomes das operações guardadas no histórico de desfazer. Usar constantes em
# vez de strings soltas evita erro de digitação silencioso ao comparar.
OPERACAO_ADICIONAR = "adicionar"
OPERACAO_REMOVER = "remover"


def _limpar(valor: Any) -> Any:
    """Tira espaços das pontas de textos; valor ausente vira texto vazio."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor.strip()
    return valor


class ComponenteOrganizacao:
    def __init__(
        self, campo_chave: str = "id", campos_obrigatorios: Sequence[str] = ()
    ) -> None:
        self.campo_chave = campo_chave
        self.campos_obrigatorios = tuple(campos_obrigatorios)
        self.registros: ListaEncadeada[Registro] = ListaEncadeada()
        self.indice: IndicePorChave[Any, Registro] = IndicePorChave()
        self.pendencias: Fila[Tuple[Registro, str]] = Fila()
        self.historico: Pilha[Tuple[str, Registro, Optional[int]]] = Pilha()

    def __len__(self) -> int:
        return len(self.registros)

    def __repr__(self) -> str:
        return (
            f"ComponenteOrganizacao(registros={len(self.registros)}, "
            f"pendencias={len(self.pendencias)})"
        )

    # ------------------------------------------------------------------
    # Organização
    # ------------------------------------------------------------------
    def adicionar(self, registro: Registro) -> bool:
        """Valida e guarda um registro.

        Retorna True se o registro entrou. Se tiver problema (chave vazia,
        chave repetida ou campo obrigatório vazio), vai para a fila de
        pendências e o método retorna False.
        """
        registro = {
            campo.strip(): _limpar(valor)
            for campo, valor in registro.items()
            if campo is not None  # o csv usa a chave None para colunas a mais
        }
        motivo = self._motivo_de_pendencia(registro)
        if motivo is not None:
            self.pendencias.enfileirar((registro, motivo))
            return False

        chave = registro[self.campo_chave]
        self.registros.inserir_fim(registro)
        self.indice.inserir(chave, registro)
        self.historico.empilhar((OPERACAO_ADICIONAR, registro, None))
        return True

    def remover(self, chave: Any) -> Optional[Registro]:
        """Remove o registro da chave informada e o retorna (None se não existir)."""
        chave = str(chave).strip()
        registro = self.indice.remover(chave)
        if registro is None:
            return None
        resultado = self.registros.remover_primeiro(lambda r: r is registro)
        posicao = resultado[0] if resultado is not None else None
        self.historico.empilhar((OPERACAO_REMOVER, registro, posicao))
        return registro

    def desfazer(self) -> Optional[str]:
        """Desfaz a última operação (adicionar ou remover).

        Retorna o nome da operação desfeita, ou None se não houver o que desfazer.
        """
        if self.historico.esta_vazia():
            return None
        operacao, registro, posicao = self.historico.desempilhar()
        chave = registro[self.campo_chave]
        if operacao == OPERACAO_ADICIONAR:
            self.indice.remover(chave)
            self.registros.remover_primeiro(lambda r: r is registro)
        else:  # OPERACAO_REMOVER: o registro volta para a mesma posição de antes
            assert posicao is not None
            self.registros.inserir_em(posicao, registro)
            self.indice.inserir(chave, registro)
        return operacao

    def proxima_pendencia(self) -> Optional[Tuple[Registro, str]]:
        """Tira da fila a pendência mais antiga: (registro, motivo).

        Retorna None se não houver pendências.
        """
        if self.pendencias.esta_vazia():
            return None
        return self.pendencias.desenfileirar()

    def _motivo_de_pendencia(self, registro: Registro) -> Optional[str]:
        chave = registro.get(self.campo_chave, "")
        if chave == "":
            return f"campo-chave '{self.campo_chave}' vazio"
        if chave in self.indice:
            return f"chave repetida: {chave}"
        for campo in self.campos_obrigatorios:
            if registro.get(campo, "") == "":
                return f"campo obrigatório vazio: {campo} (chave {chave})"
        return None

    # ------------------------------------------------------------------
    # Recuperação
    # ------------------------------------------------------------------
    def buscar_por_chave(self, chave: Any) -> Optional[Registro]:
        """Acesso direto pelo índice. O(1) em média."""
        return self.indice.buscar(str(chave).strip())

    def buscar_por_campo(self, campo: str, valor: Any) -> List[Registro]:
        """Busca sequencial na lista, sem diferenciar maiúsculas. O(n).

        Exemplo: buscar_por_campo("bairro", "Centro")
        """
        procurado = str(valor).strip().casefold()
        return self.registros.buscar(
            lambda r: str(r.get(campo, "")).strip().casefold() == procurado
        )

    # ------------------------------------------------------------------
    # Carga de arquivo
    # ------------------------------------------------------------------
    def carregar_csv(self, caminho: str) -> Tuple[int, int]:
        """Lê um CSV separado por vírgula ou ponto e vírgula e adiciona cada linha.

        Aceita arquivos em UTF-8 ou no padrão do Excel em português (Latin-1).
        Retorna (quantidade_aceita, quantidade_com_pendencia).
        """
        texto = self._ler_texto(caminho)
        primeira_linha = texto.split("\n", 1)[0]
        separador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","

        aceitos = pendentes = 0
        for linha in csv.DictReader(io.StringIO(texto), delimiter=separador):
            if self.adicionar(linha):
                aceitos += 1
            else:
                pendentes += 1
        return aceitos, pendentes

    @staticmethod
    def _ler_texto(caminho: str) -> str:
        try:
            with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
                return arquivo.read()
        except UnicodeDecodeError:
            with open(caminho, encoding="latin-1", newline="") as arquivo:
                return arquivo.read()


USO = """Uso (a partir da pasta componente/):
  python src/componente.py codigo <participantes.csv> <codigo>
  python src/componente.py nome   <participantes.csv> <nome>
  python src/componente.py demo
  python src/componente.py csv    <arquivo.csv> [coluna_chave] [obrigatorio1,obrigatorio2,...]
O CSV de participantes tem as colunas: codigo,nome."""


def _carregar_participantes(caminho: str) -> Sirca:
    sirca = Sirca()
    texto = ComponenteOrganizacao._ler_texto(caminho)
    for linha in csv.DictReader(io.StringIO(texto)):
        try:
            sirca.cadastrar_participante(linha.get("codigo", ""), linha.get("nome", ""))
        except ErroDeRegra as erro:
            print(f"Linha ignorada: {erro}")
    return sirca


def _mostrar_busca(resultado: ResultadoBusca, com_tempo: bool) -> None:
    if not resultado.encontrados:
        print("Participante não encontrado.")
    for p in resultado.encontrados:
        print(f"{p.codigo} - {p.nome}")
    print(f"Comparações: {resultado.comparacoes}")
    if com_tempo:
        print(f"Tempo da busca: {resultado.tempo}")


def _demo() -> int:
    s = Sirca()
    s.cadastrar_participante("P001", "Ana Souza")
    s.cadastrar_participante("P002", "Bruno Lima")
    s.cadastrar_edicao("E1", "Artes", date(2026, 9, 1))
    s.vincular("E1", "P001")
    s.vincular("E1", "P002")
    s.lancar_presenca("E1", "P001", "presente", "educadora1")
    s.lancar_presenca("E1", "P002", "ausente", "educadora1")
    s.corrigir_presenca("E1", "P002", "ausente justificado", "educadora1")
    print("Histórico de P002:")
    for r in s.historico_do_participante("P002"):
        print(f"  {r.edicao} {r.condicao} (versão {r.versao}) por {r.responsavel} em {r.instante:%d/%m/%Y %H:%M}")
    s.registrar_chegada("Maria")
    s.registrar_chegada("Joana", gestante=True)
    s.registrar_chegada("Pedro")
    print("Ordem de chamada:")
    while (c := s.chamar_proxima()) is not None:
        print(f"  {c.nome}")
    print("Fila vazia." if s.chamar_proxima() is None else "")
    return 0


def main(argv: Sequence[str]) -> int:
    if len(argv) < 2:
        print(USO)
        return 1
    comando = argv[1]
    if comando == "demo":
        return _demo()
    if comando in ("codigo", "nome"):
        if len(argv) < 4:
            print(USO)
            return 1
        try:
            sirca = _carregar_participantes(argv[2])
        except OSError as erro:
            print(f"Erro ao ler o arquivo '{argv[2]}': {erro}")
            return 1
        if comando == "codigo":
            _mostrar_busca(sirca.buscar_por_codigo(argv[3]), com_tempo=False)
        else:
            _mostrar_busca(sirca.buscar_por_nome(argv[3]), com_tempo=True)
        return 0
    if comando == "csv":
        return _main_csv(argv[1:])
    print(USO)
    return 1


def _main_csv(argv: Sequence[str]) -> int:
    if len(argv) < 2:
        print(USO)
        return 1

    campo_chave = argv[2] if len(argv) > 2 else "id"
    obrigatorios = [c.strip() for c in argv[3].split(",") if c.strip()] if len(argv) > 3 else []
    componente = ComponenteOrganizacao(campo_chave, obrigatorios)

    try:
        aceitos, pendentes = componente.carregar_csv(argv[1])
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {argv[1]}")
        return 1
    except OSError as erro:
        print(f"Erro ao ler o arquivo '{argv[1]}': {erro}")
        return 1

    print(f"Registros aceitos: {aceitos}")
    print(f"Registros com pendência: {pendentes}")
    while True:
        pendencia = componente.proxima_pendencia()
        if pendencia is None:
            break
        _, motivo = pendencia
        print(f"  - {motivo}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
