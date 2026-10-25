"""
Componente de organização e recuperação de registros (E2.6, versão parcial).

Junta as quatro estruturas de estruturas.py:
- ListaEncadeada -> todos os registros válidos, na ordem de chegada;
- IndicePorChave -> acesso direto a um registro pela chave;
- Fila           -> registros com problema, para a equipe revisar na ordem
                    em que apareceram;
- Pilha          -> histórico de operações, para desfazer a última.

Cada registro é um dicionário {campo: valor}, como uma linha de planilha.

Uso pela linha de comando:
    python componente.py dados_ficticios.csv
    python componente.py dados_ficticios.csv id responsavel,bairro
    (arquivo, coluna usada como chave, colunas obrigatórias separadas por vírgula)
"""

import csv
import io
import sys

from estruturas import Fila, IndicePorChave, ListaEncadeada, Pilha


def _limpar(valor):
    """Tira espaços das pontas de textos; valor ausente vira texto vazio."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor.strip()
    return valor


class ComponenteOrganizacao:
    def __init__(self, campo_chave="id", campos_obrigatorios=()):
        self.campo_chave = campo_chave
        self.campos_obrigatorios = tuple(campos_obrigatorios)
        self.registros = ListaEncadeada()
        self.indice = IndicePorChave()
        self.pendencias = Fila()
        self.historico = Pilha()

    def __len__(self):
        return len(self.registros)

    # ------------------------------------------------------------------
    # Organização
    # ------------------------------------------------------------------
    def adicionar(self, registro):
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
        self.historico.empilhar(("adicionar", registro, None))
        return True

    def remover(self, chave):
        """Remove o registro da chave informada e o retorna (None se não existir)."""
        chave = str(chave).strip()
        registro = self.indice.remover(chave)
        if registro is None:
            return None
        posicao, _ = self.registros.remover_primeiro(lambda r: r is registro)
        self.historico.empilhar(("remover", registro, posicao))
        return registro

    def desfazer(self):
        """Desfaz a última operação (adicionar ou remover).

        Retorna o nome da operação desfeita, ou None se não houver o que desfazer.
        """
        if self.historico.esta_vazia():
            return None
        operacao, registro, posicao = self.historico.desempilhar()
        chave = registro[self.campo_chave]
        if operacao == "adicionar":
            self.indice.remover(chave)
            self.registros.remover_primeiro(lambda r: r is registro)
        else:  # "remover": o registro volta para a mesma posição de antes
            self.registros.inserir_em(posicao, registro)
            self.indice.inserir(chave, registro)
        return operacao

    def proxima_pendencia(self):
        """Tira da fila a pendência mais antiga: (registro, motivo).

        Retorna None se não houver pendências.
        """
        if self.pendencias.esta_vazia():
            return None
        return self.pendencias.desenfileirar()

    def _motivo_de_pendencia(self, registro):
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
    def buscar_por_chave(self, chave):
        """Acesso direto pelo índice. O(1) em média."""
        return self.indice.buscar(str(chave).strip())

    def buscar_por_campo(self, campo, valor):
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
    def carregar_csv(self, caminho):
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
    def _ler_texto(caminho):
        try:
            with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
                return arquivo.read()
        except UnicodeDecodeError:
            with open(caminho, encoding="latin-1", newline="") as arquivo:
                return arquivo.read()


def main(argv):
    if len(argv) < 2:
        print("Uso: python componente.py <arquivo.csv> [coluna_chave] [obrigatorio1,obrigatorio2,...]")
        return 1
    campo_chave = argv[2] if len(argv) > 2 else "id"
    obrigatorios = [c.strip() for c in argv[3].split(",") if c.strip()] if len(argv) > 3 else []
    componente = ComponenteOrganizacao(campo_chave, obrigatorios)
    aceitos, pendentes = componente.carregar_csv(argv[1])

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
