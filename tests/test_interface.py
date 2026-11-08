"""Integração dos formulários com as regras, sem abrir um navegador."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class TestInterface(unittest.TestCase):
    def test_fluxo_e_erro_na_interface(self):
        app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / 'app.py'),
            default_timeout=15,
        ).run()
        self.assertFalse(app.exception)

        def clicar(texto):
            next(b for b in app.button if b.label == texto).click().run()
            self.assertFalse(app.exception)

        def detalhes_consulta():
            return next(h.value for h in app.get('html') if '<section class="consulta-resultado"' in h.value)

        app.text_input(key='entrada_produto').set_value('A')
        app.number_input(key='entrada_quantidade').set_value(20)
        clicar('Registrar entrada')
        app.selectbox(key='produto_selecionado').set_value('A').run()
        self.assertEqual([m.value for m in app.metric], ['20', '20', '0', '0'])
        app.radio(key='operacao').set_value('Reserva').run()
        app.number_input(key='movimento_quantidade').set_value(6)
        app.text_input(key='movimento_referencia').set_value('PEDIDO-1')
        clicar('Confirmar operação')
        registro = app.session_state.estoque.listar_registros('A')[0]
        self.assertEqual([m.value for m in app.metric], ['20', '14', '6', '0'])
        app.radio(key='operacao').set_value('Bloqueio').run()
        app.number_input(key='movimento_quantidade').set_value(4)
        app.text_input(key='movimento_referencia').set_value('INSPECAO')
        clicar('Confirmar operação')
        bloqueio = next(r for r in app.session_state.estoque.listar_registros('A') if r.tipo == 'bloqueio')
        self.assertEqual([m.value for m in app.metric], ['20', '10', '6', '4'])
        app.radio(key='operacao').set_value('Saída').run()
        app.number_input(key='movimento_quantidade').set_value(11)
        clicar('Confirmar operação')
        self.assertTrue(app.error)
        self.assertEqual([m.value for m in app.metric], ['20', '10', '6', '4'])
        app.number_input(key='movimento_quantidade').set_value(5)
        app.text_input(key='movimento_referencia').set_value('DOC-SAIDA-1')
        clicar('Confirmar operação')
        self.assertEqual([m.value for m in app.metric], ['15', '5', '6', '4'])
        app.text_input(key='consulta_id').set_value(registro.id)
        clicar('Consultar ID')
        self.assertFalse(app.error)
        detalhes = detalhes_consulta()
        for campo in ('A', 'Reserva', '6 unidades', 'PEDIDO-1', 'Ativo'):
            self.assertIn(campo, detalhes)
        self.assertEqual(app.code[-1].value, registro.id)
        app.selectbox(key='tipo_visualizado').set_value('Saída').run()
        self.assertEqual(list(app.dataframe[0].value['Quantidade']), [5])
        self.assertEqual(list(app.dataframe[0].value['Status']), ['Concluída'])
        self.assertEqual(list(app.dataframe[0].value['Referência']), ['DOC-SAIDA-1'])
        saida = next(r for r in app.session_state.estoque.listar_registros('A') if r.tipo == 'saida')
        app.text_input(key='consulta_id').set_value(saida.id)
        clicar('Consultar ID')
        self.assertFalse(app.error)
        detalhes = detalhes_consulta()
        for campo in ('A', 'Saída', '5 unidades', 'DOC-SAIDA-1', 'Concluída'):
            self.assertIn(campo, detalhes)
        self.assertEqual(app.code[-1].value, saida.id)
        app.text_input(key='id_liberar').set_value(registro.id)
        clicar('Liberar registro completo')
        self.assertEqual([m.value for m in app.metric], ['15', '11', '0', '4'])
        app.text_input(key='id_liberar').set_value(registro.id)
        clicar('Liberar registro completo')
        self.assertTrue(app.error)
        self.assertEqual([m.value for m in app.metric], ['15', '11', '0', '4'])
        app.text_input(key='consulta_id').set_value(bloqueio.id)
        clicar('Consultar ID')
        detalhes = detalhes_consulta()
        for campo in ('A', 'Bloqueio', '4 unidades', 'INSPECAO', 'Ativo'):
            self.assertIn(campo, detalhes)
        self.assertEqual(app.code[-1].value, bloqueio.id)
        app.text_input(key='id_liberar').set_value(bloqueio.id)
        clicar('Liberar registro completo')
        self.assertEqual([m.value for m in app.metric], ['15', '15', '0', '0'])
        self.assertIn('Liberado', detalhes_consulta())
        app.text_input(key='id_liberar').set_value(bloqueio.id)
        clicar('Liberar registro completo')
        self.assertTrue(app.error)
        self.assertEqual([m.value for m in app.metric], ['15', '15', '0', '0'])


    def test_visao_geral_e_filtro_por_produto(self):
        from estoque import ControleEstoque
        estoque = ControleEstoque()
        estoque.entrada('A', 20)
        estoque.entrada('B', 10)
        estoque.reservar('A', 6, 'PEDIDO')
        estoque.bloquear('B', 3)
        app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=15,
        )
        app.session_state['estoque'] = estoque
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric], ['30', '21', '6', '3'])
        self.assertFalse(any(b.label == 'Confirmar operação' for b in app.button))
        self.assertEqual(set(app.dataframe[0].value['Produto']), {'A', 'B'})
        self.assertEqual(set(app.dataframe[1].value['Produto']), {'A'})
        app.selectbox(key='tipo_visualizado').set_value('Bloqueio').run()
        self.assertEqual(set(app.dataframe[1].value['Produto']), {'B'})
        app.selectbox(key='produto_selecionado').set_value('B').run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric], ['10', '7', '0', '3'])
        self.assertEqual(list(app.dataframe[0].value['Produto']), ['B'])
        self.assertTrue(any(b.label == 'Confirmar operação' for b in app.button))
        app.selectbox(key='produto_selecionado').set_value(None).run()
        self.assertEqual([m.value for m in app.metric], ['30', '21', '6', '3'])
