"""
Testes dos requisitos RF-01 a RF-05 (regras do SIRCA).

Rodar a partir de componente/:
    python -m unittest discover -s testes -v

Todos os dados são fictícios.
"""

import os
import sys
import unittest
from datetime import date, datetime, timedelta

# Faz os testes (testes/) enxergarem os módulos de src/ de qualquer pasta.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import io
from contextlib import redirect_stdout

import componente
from estruturas import ColecaoOrdenada, FilaComPrioridade, IndicePorChave, ordenar_por_merge
from sirca import (
    AUSENTE,
    AUSENTE_JUSTIFICADO,
    PRESENTE,
    ErroDeRegra,
    Sirca,
)


class RelogioFalso:
    """Relógio controlado: cada chamada avança um minuto."""

    def __init__(self) -> None:
        self.agora = datetime(2026, 9, 1, 8, 0)

    def __call__(self) -> datetime:
        self.agora += timedelta(minutes=1)
        return self.agora


def sirca_basico() -> Sirca:
    s = Sirca(RelogioFalso())
    for codigo, nome in [("P001", "Ana Souza"), ("P002", "Bruno Lima"), ("P003", "Carla Dias")]:
        s.cadastrar_participante(codigo, nome)
    s.cadastrar_edicao("E1", "Artes", date(2026, 9, 1))
    s.cadastrar_edicao("E2", "Música", date(2026, 9, 8))
    for p in ("P001", "P002"):
        s.vincular("E1", p)
    s.vincular("E2", "P001")
    return s


class TestRF01Frequencia(unittest.TestCase):
    def test_registra_com_data_hora_e_responsavel(self):
        s = sirca_basico()
        r = s.lancar_presenca("E1", "P001", PRESENTE, "educadora1")
        self.assertEqual(r.responsavel, "educadora1")
        self.assertEqual(r.condicao, PRESENTE)
        consultado = s.consultar_registro("E1", "P001")
        assert consultado is not None
        self.assertEqual(consultado.instante, r.instante)

    def test_aceita_as_tres_condicoes_da_rn01(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", PRESENTE, "e1")
        s.lancar_presenca("E1", "P002", AUSENTE_JUSTIFICADO, "e1")
        s.lancar_presenca("E2", "P001", AUSENTE, "e1")

    def test_recusa_condicao_invalida(self):
        s = sirca_basico()
        with self.assertRaises(ErroDeRegra):
            s.lancar_presenca("E1", "P001", "talvez", "e1")

    def test_recusa_participante_nao_vinculado(self):
        s = sirca_basico()
        with self.assertRaises(ErroDeRegra):
            s.lancar_presenca("E1", "P003", PRESENTE, "e1")
        self.assertIsNone(s.consultar_registro("E1", "P003"))

    def test_recusa_participante_ou_edicao_inexistente(self):
        s = sirca_basico()
        with self.assertRaises(ErroDeRegra):
            s.lancar_presenca("E1", "P999", PRESENTE, "e1")
        with self.assertRaises(ErroDeRegra):
            s.lancar_presenca("E99", "P001", PRESENTE, "e1")

    def test_recusa_sem_responsavel(self):
        s = sirca_basico()
        with self.assertRaises(ErroDeRegra):
            s.lancar_presenca("E1", "P001", PRESENTE, "   ")
        self.assertIsNone(s.consultar_registro("E1", "P001"))

    def test_no_maximo_um_registro_por_participante_por_edicao(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", PRESENTE, "e1")
        with self.assertRaises(ErroDeRegra):
            s.lancar_presenca("E1", "P001", AUSENTE, "e1")
        registro = s.consultar_registro("E1", "P001")
        assert registro is not None
        self.assertEqual(registro.condicao, PRESENTE)

    def test_correcao_preserva_valor_anterior_em_historico(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", AUSENTE, "e1")
        novo = s.corrigir_presenca("E1", "P001", AUSENTE_JUSTIFICADO, "e2")
        self.assertEqual(novo.versao, 2)
        anteriores = s.versoes_anteriores("E1", "P001")
        self.assertEqual([r.condicao for r in anteriores], [AUSENTE])
        vigente = s.consultar_registro("E1", "P001")
        assert vigente is not None
        self.assertEqual(vigente.condicao, AUSENTE_JUSTIFICADO)

    def test_corrigir_sem_registro_previo_e_recusado(self):
        s = sirca_basico()
        with self.assertRaises(ErroDeRegra):
            s.corrigir_presenca("E1", "P001", PRESENTE, "e1")

    def test_desfazer_e_refazer_lancamento(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", PRESENTE, "e1")
        self.assertEqual(s.desfazer(), "lancar")
        self.assertIsNone(s.consultar_registro("E1", "P001"))
        self.assertEqual(s.historico_do_participante("P001"), [])
        self.assertEqual(s.refazer(), "lancar")
        self.assertIsNotNone(s.consultar_registro("E1", "P001"))
        self.assertEqual(len(s.historico_do_participante("P001")), 1)

    def test_desfazer_correcao_restaura_valor_anterior(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", AUSENTE, "e1")
        s.corrigir_presenca("E1", "P001", PRESENTE, "e1")
        self.assertEqual(s.desfazer(), "corrigir")
        vigente = s.consultar_registro("E1", "P001")
        assert vigente is not None
        self.assertEqual(vigente.condicao, AUSENTE)
        self.assertEqual(s.versoes_anteriores("E1", "P001"), [])
        s.refazer()
        vigente = s.consultar_registro("E1", "P001")
        assert vigente is not None
        self.assertEqual(vigente.condicao, PRESENTE)

    def test_desfazer_e_refazer_sem_nada_nao_dao_erro(self):
        s = sirca_basico()
        self.assertIsNone(s.desfazer())
        self.assertIsNone(s.refazer())

    def test_acao_nova_invalida_o_refazer(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", PRESENTE, "e1")
        s.desfazer()
        s.lancar_presenca("E1", "P002", PRESENTE, "e1")
        self.assertIsNone(s.refazer())


class TestRF02Historico(unittest.TestCase):
    def test_ordem_do_mais_recente_para_o_mais_antigo(self):
        s = sirca_basico()
        # lança primeiro a edição mais nova: a ordem vale pela data da edição
        s.lancar_presenca("E2", "P001", PRESENTE, "e1")
        s.lancar_presenca("E1", "P001", AUSENTE, "e1")
        historico = s.historico_do_participante("P001")
        self.assertEqual([r.edicao for r in historico], ["E2", "E1"])

    def test_codigo_inexistente_devolve_vazio_sem_erro(self):
        self.assertEqual(sirca_basico().historico_do_participante("P999"), [])

    def test_participante_sem_frequencia_devolve_vazio(self):
        self.assertEqual(sirca_basico().historico_do_participante("P003"), [])

    def test_correcao_nao_duplica_no_historico(self):
        s = sirca_basico()
        s.lancar_presenca("E1", "P001", AUSENTE, "e1")
        s.corrigir_presenca("E1", "P001", PRESENTE, "e1")
        historico = s.historico_do_participante("P001")
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0].condicao, PRESENTE)


class TestRF03FilaPrioritaria(unittest.TestCase):
    def nomes_chamados(self, s: Sirca) -> list:
        saida = []
        while True:
            c = s.chamar_proxima()
            if c is None:
                return saida
            saida.append(c.nome)

    def test_sem_prioridade_vale_a_ordem_de_chegada(self):
        s = Sirca()
        for nome in ["A", "B", "C"]:
            s.registrar_chegada(nome)
        self.assertEqual(self.nomes_chamados(s), ["A", "B", "C"])

    def test_prioritario_passa_na_frente_dos_comuns(self):
        s = Sirca()
        s.registrar_chegada("A")
        s.registrar_chegada("B")
        s.registrar_chegada("Idosa", idoso=True)
        self.assertEqual(self.nomes_chamados(s), ["Idosa", "A", "B"])

    def test_prioritario_fica_depois_dos_prioritarios_que_chegaram_antes(self):
        s = Sirca()
        s.registrar_chegada("Comum")
        s.registrar_chegada("Gestante", gestante=True)
        s.registrar_chegada("PcD", pessoa_com_deficiencia=True)
        s.registrar_chegada("Idoso", idoso=True)
        self.assertEqual(self.nomes_chamados(s), ["Gestante", "PcD", "Idoso", "Comum"])

    def test_pessoa_em_mais_de_um_grupo_ocupa_uma_posicao(self):
        s = Sirca()
        s.registrar_chegada("Comum")
        s.registrar_chegada("IdosaGestante", idoso=True, gestante=True)
        self.assertEqual(self.nomes_chamados(s), ["IdosaGestante", "Comum"])

    def test_dentro_do_grupo_ninguem_passa_o_que_chegou_primeiro(self):
        s = Sirca()
        for i in range(5):
            s.registrar_chegada(f"C{i}")
            s.registrar_chegada(f"P{i}", idoso=True)
        esperado = [f"P{i}" for i in range(5)] + [f"C{i}" for i in range(5)]
        self.assertEqual(self.nomes_chamados(s), esperado)

    def test_fila_vazia_informa_sem_erro(self):
        self.assertIsNone(Sirca().chamar_proxima())

    def test_chamada_intercalada_com_chegadas(self):
        s = Sirca()
        s.registrar_chegada("A")
        s.registrar_chegada("B")
        primeiro = s.chamar_proxima()
        assert primeiro is not None
        self.assertEqual(primeiro.nome, "A")
        s.registrar_chegada("Gestante", gestante=True)
        proximo = s.chamar_proxima()
        assert proximo is not None
        self.assertEqual(proximo.nome, "Gestante")

    def test_nome_vazio_e_recusado(self):
        with self.assertRaises(ErroDeRegra):
            Sirca().registrar_chegada("  ")

    def test_estrutura_fila_com_prioridade_diretamente(self):
        fila: FilaComPrioridade[str] = FilaComPrioridade()
        fila.enfileirar("x")
        fila.enfileirar("y", prioritario=True)
        self.assertEqual(list(fila), ["y", "x"])
        self.assertEqual(fila.frente(), "y")
        self.assertEqual(len(fila), 2)


def sirca_com_225_participantes() -> Sirca:
    s = Sirca()
    for i in range(1, 226):
        s.cadastrar_participante(f"P{i:03d}", f"Pessoa {i:03d}")
    return s


class TestRF04BuscaPorCodigo(unittest.TestCase):
    def test_codigo_existente_retorna_o_participante(self):
        r = sirca_basico().buscar_por_codigo("P002")
        self.assertEqual([p.nome for p in r.encontrados], ["Bruno Lima"])

    def test_codigo_inexistente_informa_sem_erro(self):
        r = sirca_basico().buscar_por_codigo("P999")
        self.assertEqual(r.encontrados, [])

    def test_comparacoes_menores_que_o_numero_de_participantes(self):
        s = sirca_com_225_participantes()
        for i in range(1, 226):
            r = s.buscar_por_codigo(f"P{i:03d}")
            self.assertEqual(len(r.encontrados), 1)
            self.assertLess(r.comparacoes, 225)
        self.assertLess(s.buscar_por_codigo("P999").comparacoes, 225)

    def test_indice_conta_comparacoes_em_colisao(self):
        indice: IndicePorChave[str, int] = IndicePorChave(capacidade=1)
        indice.OCUPACAO_MAXIMA = 100.0  # impede o redimensionamento neste teste
        for i in range(3):
            indice.inserir(f"k{i}", i)
        indice.buscar("k0")  # k0 é o último inserido -> 1ª da cadeia ou última
        self.assertGreaterEqual(indice.comparacoes_ultima_busca, 1)
        self.assertLessEqual(indice.comparacoes_ultima_busca, 3)


class TestRF05BuscaPorNome(unittest.TestCase):
    def test_nome_existente_retorna_dados_e_tempo_com_unidade(self):
        r = sirca_basico().buscar_por_nome("Bruno Lima")
        self.assertEqual([p.codigo for p in r.encontrados], ["P002"])
        self.assertGreaterEqual(r.tempo_ns, 0)
        self.assertTrue(r.tempo.endswith(("ms", "µs")))

    def test_ignora_maiusculas_e_espacos_nas_pontas(self):
        r = sirca_basico().buscar_por_nome("  bruno LIMA ")
        self.assertEqual(len(r.encontrados), 1)

    def test_nome_inexistente_informa_e_mede_tempo(self):
        r = sirca_basico().buscar_por_nome("Fulano Inexistente")
        self.assertEqual(r.encontrados, [])
        self.assertTrue(r.tempo)

    def test_nome_repetido_retorna_todos(self):
        s = sirca_basico()
        s.cadastrar_participante("P010", "Ana Souza")
        s.cadastrar_participante("P011", "Ana Souza")
        r = s.buscar_por_nome("Ana Souza")
        self.assertEqual(sorted(p.codigo for p in r.encontrados), ["P001", "P010", "P011"])

    def test_resultado_nao_depende_da_ordem_de_cadastro(self):
        nomes = ["Zeca", "Ana", "Mara", "Bia", "Ana", "Leo"]
        for ordem in (nomes, list(reversed(nomes)), sorted(nomes)):
            s = Sirca()
            for i, n in enumerate(ordem):
                s.cadastrar_participante(f"X{i}", n)
            self.assertEqual(len(s.buscar_por_nome("Ana").encontrados), 2)
            self.assertEqual(len(s.buscar_por_nome("Zeca").encontrados), 1)

    def test_busca_apos_novo_cadastro_reordena(self):
        s = sirca_basico()
        s.buscar_por_nome("Ana Souza")
        s.cadastrar_participante("P020", "Aaron Teste")
        self.assertEqual(len(s.buscar_por_nome("Aaron Teste").encontrados), 1)


class TestColecaoOrdenada(unittest.TestCase):
    def test_merge_sort_ordena_e_e_estavel(self):
        itens = [("b", 1), ("a", 2), ("b", 0), ("a", 1)]
        ordenado = ordenar_por_merge(itens, lambda t: t[0])
        self.assertEqual(ordenado, [("a", 2), ("a", 1), ("b", 1), ("b", 0)])

    def test_merge_sort_vazio_e_unitario(self):
        self.assertEqual(ordenar_por_merge([], str), [])
        self.assertEqual(ordenar_por_merge(["x"], str), ["x"])

    def test_busca_binaria_faz_poucas_comparacoes(self):
        c: ColecaoOrdenada[str] = ColecaoOrdenada(lambda s: s)
        for i in range(1024):
            c.adicionar(f"n{i:04d}")
        self.assertEqual(c.buscar("n0500"), ["n0500"])
        self.assertLess(c.comparacoes_ultima_busca, 20)
        self.assertEqual(c.buscar("zzz"), [])

    def test_colecao_vazia(self):
        c: ColecaoOrdenada[str] = ColecaoOrdenada(lambda s: s)
        self.assertEqual(c.buscar("a"), [])


PASTA = os.path.dirname(os.path.abspath(__file__))
MASSA = os.path.join(PASTA, "participantes_ficticios.csv")


class TestLinhaDeComando(unittest.TestCase):
    def rodar(self, *args: str) -> str:
        saida = io.StringIO()
        with redirect_stdout(saida):
            componente.main(["componente.py", *args])
        return saida.getvalue()

    def test_busca_por_codigo_na_massa_de_225(self):
        texto = self.rodar("codigo", MASSA, "P010")
        self.assertIn("P010 - ", texto)
        self.assertIn("Comparações:", texto)

    def test_busca_por_codigo_inexistente(self):
        self.assertIn("não encontrado", self.rodar("codigo", MASSA, "P999"))

    def test_busca_por_nome_mostra_tempo_e_todos_os_homonimos(self):
        sirca = componente._carregar_participantes(MASSA)
        self.assertEqual(len(sirca._por_nome), 225)
        texto = self.rodar("nome", MASSA, "Ana Silva")
        self.assertIn("Tempo da busca:", texto)

    def test_demo_roda(self):
        texto = self.rodar("demo")
        self.assertIn("Joana", texto)
        self.assertIn("Fila vazia.", texto)


if __name__ == "__main__":
    unittest.main()
