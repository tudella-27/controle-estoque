import unittest
from dataclasses import FrozenInstanceError

from estoque import ControleEstoque, ErroEstoque, SituacaoEstoque


class TestEntradaConsulta(unittest.TestCase):
    def setUp(self):
        self.estoque = ControleEstoque()

    def test_primeira_entrada_cria_produto(self):
        self.estoque.entrada("PROD-001", 20)
        saldo = self.estoque.consultar_produto("PROD-001")
        self.assertEqual(saldo, SituacaoEstoque("PROD-001", 20))
        self.assertEqual(saldo.disponivel, 20)
        self.assertEqual(saldo.total, saldo.disponivel + saldo.reservado + saldo.bloqueado)

    def test_entradas_acumulam_e_normalizam_codigo(self):
        self.estoque.entrada(" prod-001 ", 20)
        self.estoque.entrada("PROD-001", 5)
        self.assertEqual(self.estoque.consultar_produto("prod-001").total, 25)

    def test_produtos_independentes(self):
        self.estoque.entrada("A", 10)
        self.estoque.entrada("B", 7)
        self.estoque.entrada("A", 2)
        self.assertEqual(self.estoque.consultar_produto("A").total, 12)
        self.assertEqual(self.estoque.consultar_produto("B").total, 7)

    def test_quantidade_invalida_preserva_estado_e_nao_cria_produto(self):
        self.estoque.entrada("A", 10)
        antes = self.estoque.consultar_produto("A")
        for quantidade in (0, -1, 1.5, 2.0, "2", None, True, False):
            with self.subTest(quantidade=quantidade):
                for produto in ("A", "NOVO"):
                    with self.assertRaises(ErroEstoque):
                        self.estoque.entrada(produto, quantidade)
                self.assertEqual(self.estoque.consultar_produto("A"), antes)
                with self.assertRaises(ErroEstoque):
                    self.estoque.consultar_produto("NOVO")

    def test_codigo_invalido(self):
        for codigo in ("", "   ", None, 123):
            with self.subTest(codigo=codigo):
                with self.assertRaises(ErroEstoque):
                    self.estoque.entrada(codigo, 10)
                with self.assertRaises(ErroEstoque):
                    self.estoque.consultar_produto(codigo)

    def test_consulta_produto_inexistente(self):
        with self.assertRaisesRegex(ErroEstoque, "Produto não encontrado"):
            self.estoque.consultar_produto("INEXISTENTE")

    def test_consulta_nao_permite_alterar_saldo_interno(self):
        self.estoque.entrada("A", 10)
        saldo = self.estoque.consultar_produto("A")
        with self.assertRaises(FrozenInstanceError):
            saldo.total = 999
        self.assertEqual(self.estoque.consultar_produto("A").total, 10)


if __name__ == "__main__":
    unittest.main()
