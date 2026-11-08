import unittest

from estoque import ControleEstoque, ErroEstoque


class TestOperacoes(unittest.TestCase):
    def setUp(self):
        self.estoque = ControleEstoque()
        self.estoque.entrada('A', 30)
        self.estoque.entrada('B', 10)

    def estado(self):
        return tuple(
            (self.estoque.consultar_produto(p), self.estoque.listar_registros(p))
            for p in self.estoque.listar_produtos()
        )

    def conferir(self, total, disponivel, reservado, bloqueado):
        saldo = self.estoque.consultar_produto('A')
        self.assertEqual(
            (saldo.total, saldo.disponivel, saldo.reservado, saldo.bloqueado),
            (total, disponivel, reservado, bloqueado),
        )
        self.assertEqual(saldo.total, saldo.disponivel + saldo.reservado + saldo.bloqueado)

    def test_fluxo_multiplos_registros_e_liberacao_individual(self):
        r1 = self.estoque.reservar('A', 8, 'PEDIDO-A')
        self.conferir(30, 22, 8, 0)
        r2 = self.estoque.reservar('A', 5, 'PEDIDO-B')
        self.conferir(30, 17, 13, 0)
        b1 = self.estoque.bloquear('A', 4, 'INSPECAO')
        self.conferir(30, 13, 13, 4)
        b2 = self.estoque.bloquear('A', 3, 'AVARIA')
        self.conferir(30, 10, 13, 7)
        self.assertEqual(len({r.id for r in (r1, r2, b1, b2)}), 4)
        self.estoque.saida('A', 6)
        self.conferir(24, 4, 13, 7)
        self.estoque.liberar(r1.id)
        self.conferir(24, 12, 5, 7)
        for registro in (r2, b1, b2):
            self.assertEqual(self.estoque.consultar_registro(registro.id), registro)
        self.estoque.liberar(b2.id)
        self.conferir(24, 15, 5, 4)
        self.estoque.saida('A', 15)
        self.conferir(9, 0, 5, 4)
        self.estoque.liberar(r2.id)
        self.estoque.liberar(b1.id)
        self.conferir(9, 9, 0, 0)
        self.assertEqual(len(self.estoque.listar_registros('A')), 6)
        self.assertTrue(all(not r.ativo for r in self.estoque.listar_registros('A')))
        self.assertEqual(self.estoque.consultar_produto('B').total, 10)
        self.assertEqual(self.estoque.listar_registros('B'), ())

    def test_saldo_exato_para_cada_operacao(self):
        for operacao in ('saida', 'reservar', 'bloquear'):
            with self.subTest(operacao=operacao):
                estoque = ControleEstoque()
                estoque.entrada('A', 10)
                estoque.reservar('A', 2, 'ANTERIOR')
                argumentos = ('A', 8, 'PEDIDO') if operacao == 'reservar' else ('A', 8)
                getattr(estoque, operacao)(*argumentos)
                saldo = estoque.consultar_produto('A')
                self.assertEqual(saldo.disponivel, 0)
                self.assertEqual(saldo.total, 2 if operacao == 'saida' else 10)

    def test_erros_preservam_todo_estado(self):
        reserva = self.estoque.reservar('A', 8, 'PEDIDO')
        bloqueio = self.estoque.bloquear('A', 4)
        for operacao in ('saida', 'reservar', 'bloquear'):
            for produto, quantidade in [('A', 19), ('INEXISTENTE', 1)] + [
                ('A', q) for q in (0, -1, 1.5, 2.0, '2', None, True, False)
            ]:
                with self.subTest(operacao=operacao, produto=produto, quantidade=quantidade):
                    antes = self.estado()
                    args = (produto, quantidade, 'PEDIDO') if operacao == 'reservar' else (produto, quantidade)
                    with self.assertRaises(ErroEstoque):
                        getattr(self.estoque, operacao)(*args)
                    self.assertEqual(self.estado(), antes)
        for registro in (reserva, bloqueio):
            self.estoque.liberar(registro.id)
            antes = self.estado()
            with self.assertRaises(ErroEstoque):
                self.estoque.liberar(registro.id)
            self.assertEqual(self.estado(), antes)

    def test_ids_invalidos_preservam_estado(self):
        for identificador in ('INEXISTENTE', '', ' ', None, 123):
            for operacao in ('consultar_registro', 'liberar'):
                with self.subTest(id=identificador, operacao=operacao):
                    antes = self.estado()
                    with self.assertRaises(ErroEstoque):
                        getattr(self.estoque, operacao)(identificador)
                    self.assertEqual(self.estado(), antes)

    def test_referencia_reserva_obrigatoria(self):
        for referencia in ('', '  ', None, 123):
            with self.subTest(referencia=referencia):
                antes = self.estado()
                with self.assertRaises(ErroEstoque):
                    self.estoque.reservar('A', 1, referencia)
                self.assertEqual(self.estado(), antes)

    def test_bloqueio_referencia_opcional_mas_textual(self):
        registro = self.estoque.bloquear('A', 2)
        self.assertEqual(registro.referencia, '')
        antes = self.estado()
        with self.assertRaises(ErroEstoque):
            self.estoque.bloquear('A', 1, None)
        self.assertEqual(self.estado(), antes)

    def test_mesmo_pedido_pode_ter_reservas_distintas(self):
        r1 = self.estoque.reservar(' a ', 2, ' PEDIDO ')
        r2 = self.estoque.reservar('A', 3, 'PEDIDO')
        self.assertNotEqual(r1.id, r2.id)
        self.assertEqual(r1.referencia, r2.referencia)
        self.assertEqual(self.estoque.consultar_registro(r1.id), r1)
        self.conferir(30, 25, 5, 0)

    def test_entrada_com_registros_ativos(self):
        self.estoque.reservar('A', 8, 'PEDIDO')
        self.estoque.bloquear('A', 4)
        self.estoque.entrada('A', 5)
        self.conferir(35, 23, 8, 4)


class TestSaidasIdentificadas(unittest.TestCase):
    def test_consulta_saida_e_rejeicao_de_liberacao(self):
        estoque = ControleEstoque()
        estoque.entrada('A', 10)
        saida = estoque.saida('A', 3)
        self.assertTrue(saida.id.startswith('SAI-'))
        self.assertEqual(estoque.consultar_registro(saida.id), saida)
        antes = (estoque.consultar_produto('A'), estoque.listar_registros('A'))
        with self.assertRaises(ErroEstoque):
            estoque.liberar(saida.id)
        with self.assertRaises(ErroEstoque):
            estoque.saida('A', 8)
        self.assertEqual((estoque.consultar_produto('A'), estoque.listar_registros('A')), antes)
        outra = estoque.saida('A', 2)
        self.assertNotEqual(saida.id, outra.id)
        self.assertEqual(estoque.consultar_produto('A').disponivel, 5)


class TestReferenciaSaida(unittest.TestCase):
    def test_referencia_normalizada_e_consultavel(self):
        estoque = ControleEstoque()
        estoque.entrada('A', 10)
        registro = estoque.saida('A', 3, ' PEDIDO-42 ')
        self.assertEqual(estoque.consultar_registro(registro.id).referencia, 'PEDIDO-42')
        self.assertEqual(estoque.consultar_produto('A').disponivel, 7)

    def test_referencia_invalida_preserva_estado(self):
        estoque = ControleEstoque()
        estoque.entrada('A', 10)
        for referencia in (None, 42, True):
            with self.subTest(referencia=referencia):
                with self.assertRaises(ErroEstoque):
                    estoque.saida('A', 3, referencia)
                self.assertEqual(estoque.consultar_produto('A').total, 10)
                self.assertEqual(estoque.listar_registros('A'), ())


if __name__ == '__main__':
    unittest.main()
