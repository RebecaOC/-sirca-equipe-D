"""
Testes do E2.6 (estruturas e componente).

Rodar na pasta do projeto:
    python -m unittest -v

Todos os dados usados aqui são fictícios.
"""

import os
import tempfile
import unittest

from componente import ComponenteOrganizacao
from estruturas import Fila, IndicePorChave, ListaEncadeada, Pilha


class TestListaEncadeada(unittest.TestCase):
    def test_comeca_vazia(self):
        lista = ListaEncadeada()
        self.assertTrue(lista.esta_vazia())
        self.assertEqual(len(lista), 0)
        self.assertEqual(list(lista), [])

    def test_inserir_inicio_e_fim_mantem_a_ordem(self):
        lista = ListaEncadeada()
        lista.inserir_fim("b")
        lista.inserir_fim("c")
        lista.inserir_inicio("a")
        self.assertEqual(list(lista), ["a", "b", "c"])
        self.assertEqual(len(lista), 3)

    def test_inserir_em_posicao_do_meio(self):
        lista = ListaEncadeada()
        for valor in ["a", "c"]:
            lista.inserir_fim(valor)
        lista.inserir_em(1, "b")
        self.assertEqual(list(lista), ["a", "b", "c"])

    def test_obter_por_posicao(self):
        lista = ListaEncadeada()
        for valor in [10, 20, 30]:
            lista.inserir_fim(valor)
        self.assertEqual(lista.obter(0), 10)
        self.assertEqual(lista.obter(2), 30)
        with self.assertRaises(IndexError):
            lista.obter(3)

    def test_buscar_retorna_todos_que_atendem(self):
        lista = ListaEncadeada()
        for valor in [1, 2, 3, 4, 5, 6]:
            lista.inserir_fim(valor)
        self.assertEqual(lista.buscar(lambda v: v % 2 == 0), [2, 4, 6])
        self.assertEqual(lista.buscar(lambda v: v > 10), [])

    def test_remover_primeiro_retorna_posicao_e_valor(self):
        lista = ListaEncadeada()
        for valor in ["a", "b", "c"]:
            lista.inserir_fim(valor)
        self.assertEqual(lista.remover_primeiro(lambda v: v == "b"), (1, "b"))
        self.assertEqual(list(lista), ["a", "c"])
        self.assertIsNone(lista.remover_primeiro(lambda v: v == "x"))

    def test_remover_o_ultimo_atualiza_o_fim(self):
        lista = ListaEncadeada()
        for valor in ["a", "b"]:
            lista.inserir_fim(valor)
        lista.remover_primeiro(lambda v: v == "b")
        lista.inserir_fim("c")  # só funciona se o ponteiro _fim foi corrigido
        self.assertEqual(list(lista), ["a", "c"])

    def test_remover_unico_elemento_esvazia_a_lista(self):
        lista = ListaEncadeada()
        lista.inserir_fim("a")
        lista.remover_primeiro(lambda v: v == "a")
        self.assertTrue(lista.esta_vazia())
        lista.inserir_fim("b")
        self.assertEqual(list(lista), ["b"])


class TestPilha(unittest.TestCase):
    def test_ultimo_a_entrar_e_o_primeiro_a_sair(self):
        pilha = Pilha()
        for valor in [1, 2, 3]:
            pilha.empilhar(valor)
        self.assertEqual(pilha.topo(), 3)
        self.assertEqual([pilha.desempilhar() for _ in range(3)], [3, 2, 1])
        self.assertTrue(pilha.esta_vazia())

    def test_desempilhar_pilha_vazia_gera_erro(self):
        with self.assertRaises(IndexError):
            Pilha().desempilhar()
        with self.assertRaises(IndexError):
            Pilha().topo()


class TestFila(unittest.TestCase):
    def test_primeiro_a_entrar_e_o_primeiro_a_sair(self):
        fila = Fila()
        for valor in [1, 2, 3]:
            fila.enfileirar(valor)
        self.assertEqual(fila.frente(), 1)
        self.assertEqual([fila.desenfileirar() for _ in range(3)], [1, 2, 3])
        self.assertTrue(fila.esta_vazia())

    def test_fila_volta_a_funcionar_depois_de_esvaziar(self):
        fila = Fila()
        fila.enfileirar("a")
        fila.desenfileirar()
        fila.enfileirar("b")
        self.assertEqual(list(fila), ["b"])

    def test_desenfileirar_fila_vazia_gera_erro(self):
        with self.assertRaises(IndexError):
            Fila().desenfileirar()
        with self.assertRaises(IndexError):
            Fila().frente()


class TestIndicePorChave(unittest.TestCase):
    def test_inserir_e_buscar(self):
        indice = IndicePorChave()
        self.assertTrue(indice.inserir("F001", "registro 1"))
        self.assertEqual(indice.buscar("F001"), "registro 1")
        self.assertIn("F001", indice)
        self.assertIsNone(indice.buscar("F999"))
        self.assertNotIn("F999", indice)

    def test_chave_repetida_substitui_o_valor(self):
        indice = IndicePorChave()
        indice.inserir("F001", "antigo")
        self.assertFalse(indice.inserir("F001", "novo"))
        self.assertEqual(indice.buscar("F001"), "novo")
        self.assertEqual(len(indice), 1)

    def test_remover(self):
        indice = IndicePorChave()
        indice.inserir("F001", "registro 1")
        self.assertEqual(indice.remover("F001"), "registro 1")
        self.assertNotIn("F001", indice)
        self.assertEqual(len(indice), 0)
        self.assertIsNone(indice.remover("F001"))

    def test_colisoes_nao_perdem_dados(self):
        indice = IndicePorChave(capacidade=1)  # força todas as chaves no mesmo balde
        indice.OCUPACAO_MAXIMA = 1000  # e impede o redimensionamento
        for i in range(20):
            indice.inserir(f"F{i:03d}", i)
        for i in range(20):
            self.assertEqual(indice.buscar(f"F{i:03d}"), i)
        indice.remover("F010")
        self.assertNotIn("F010", indice)
        self.assertEqual(len(indice), 19)

    def test_redimensiona_sem_perder_chaves(self):
        indice = IndicePorChave()
        for i in range(500):
            indice.inserir(f"F{i:03d}", i)
        self.assertEqual(len(indice), 500)
        self.assertEqual(sorted(indice.chaves()), sorted(f"F{i:03d}" for i in range(500)))
        self.assertEqual(indice.buscar("F499"), 499)


def _registro(chave, responsavel="Responsável Fictício", bairro="Centro"):
    return {"id": chave, "responsavel": responsavel, "bairro": bairro}


class TestComponente(unittest.TestCase):
    def setUp(self):
        self.comp = ComponenteOrganizacao("id", campos_obrigatorios=["responsavel"])

    def test_registro_valido_entra_na_lista_e_no_indice(self):
        self.assertTrue(self.comp.adicionar(_registro("F001")))
        self.assertEqual(len(self.comp), 1)
        self.assertEqual(self.comp.buscar_por_chave("F001")["bairro"], "Centro")

    def test_espacos_sao_removidos(self):
        self.comp.adicionar({" id ": " F001 ", "responsavel": " Fulano Fictício "})
        registro = self.comp.buscar_por_chave("F001")
        self.assertEqual(registro["responsavel"], "Fulano Fictício")

    def test_problemas_vao_para_a_fila_de_pendencias_em_ordem(self):
        self.comp.adicionar(_registro("F001"))
        self.assertFalse(self.comp.adicionar(_registro("")))          # chave vazia
        self.assertFalse(self.comp.adicionar(_registro("F001")))      # chave repetida
        self.assertFalse(self.comp.adicionar(_registro("F002", "")))  # obrigatório vazio
        self.assertEqual(len(self.comp), 1)
        self.assertEqual(len(self.comp.pendencias), 3)

        motivos = [self.comp.proxima_pendencia()[1] for _ in range(3)]
        self.assertIn("vazio", motivos[0])
        self.assertIn("repetida", motivos[1])
        self.assertIn("responsavel", motivos[2])
        self.assertIsNone(self.comp.proxima_pendencia())

    def test_chave_repetida_nao_sobrescreve_o_primeiro_registro(self):
        self.comp.adicionar(_registro("F001", bairro="Centro"))
        self.comp.adicionar(_registro("F001", bairro="Setor Sul"))
        self.assertEqual(self.comp.buscar_por_chave("F001")["bairro"], "Centro")

    def test_buscar_por_campo_ignora_maiusculas(self):
        self.comp.adicionar(_registro("F001", bairro="Centro"))
        self.comp.adicionar(_registro("F002", bairro="Vila Nova"))
        self.comp.adicionar(_registro("F003", bairro="CENTRO"))
        encontrados = self.comp.buscar_por_campo("bairro", "centro")
        self.assertEqual([r["id"] for r in encontrados], ["F001", "F003"])

    def test_remover_e_desfazer_devolve_na_mesma_posicao(self):
        for chave in ["F001", "F002", "F003"]:
            self.comp.adicionar(_registro(chave))
        removido = self.comp.remover("F002")
        self.assertEqual(removido["id"], "F002")
        self.assertIsNone(self.comp.buscar_por_chave("F002"))
        self.assertEqual([r["id"] for r in self.comp.registros], ["F001", "F003"])

        self.assertEqual(self.comp.desfazer(), "remover")
        self.assertEqual([r["id"] for r in self.comp.registros], ["F001", "F002", "F003"])
        self.assertIsNotNone(self.comp.buscar_por_chave("F002"))

    def test_desfazer_adicionar(self):
        self.comp.adicionar(_registro("F001"))
        self.comp.adicionar(_registro("F002"))
        self.assertEqual(self.comp.desfazer(), "adicionar")
        self.assertIsNone(self.comp.buscar_por_chave("F002"))
        self.assertEqual(len(self.comp), 1)

    def test_desfazer_sem_historico(self):
        self.assertIsNone(self.comp.desfazer())

    def test_remover_chave_inexistente(self):
        self.assertIsNone(self.comp.remover("F999"))


class TestCargaCSV(unittest.TestCase):
    def _arquivo(self, conteudo, encoding="utf-8"):
        arquivo = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                              encoding=encoding, newline="")
        arquivo.write(conteudo)
        arquivo.close()
        self.addCleanup(os.remove, arquivo.name)
        return arquivo.name

    def test_csv_com_ponto_e_virgula(self):
        caminho = self._arquivo(
            "id;responsavel;bairro\n"
            "F001;Responsável A;Centro\n"
            "F002;Responsável B;Vila Nova\n"
            "F001;Responsável C;Centro\n"
        )
        comp = ComponenteOrganizacao("id")
        self.assertEqual(comp.carregar_csv(caminho), (2, 1))
        self.assertEqual(comp.buscar_por_chave("F002")["bairro"], "Vila Nova")

    def test_csv_com_virgula_e_acento_em_latin1(self):
        caminho = self._arquivo(
            "codigo,responsavel,bairro\n"
            "10,Responsável Fictício,São Jorge\n",
            encoding="latin-1",
        )
        comp = ComponenteOrganizacao("codigo")
        self.assertEqual(comp.carregar_csv(caminho), (1, 0))
        self.assertEqual(comp.buscar_por_chave(10)["bairro"], "São Jorge")

    def test_arquivo_de_exemplo(self):
        pasta = os.path.dirname(os.path.abspath(__file__))
        comp = ComponenteOrganizacao("id", campos_obrigatorios=["responsavel"])
        aceitos, pendentes = comp.carregar_csv(os.path.join(pasta, "dados_ficticios.csv"))
        self.assertEqual((aceitos, pendentes), (4, 3))
        self.assertEqual(len(comp.buscar_por_campo("bairro", "Centro")), 2)


if __name__ == "__main__":
    unittest.main()
