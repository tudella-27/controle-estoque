"""Interface local. As regras e validações ficam em estoque.py."""
from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

from estoque import ControleEstoque, ErroEstoque

st.set_page_config(page_title='Controle de Estoque', page_icon=':material/inventory_2:', layout='wide')
st.html(Path(__file__).with_name('estilo.css'))

if 'estoque' not in st.session_state:
    st.session_state.estoque = ControleEstoque()
estoque = st.session_state.estoque


def concluir(mensagem, area):
    st.session_state.mensagem = (area, mensagem)
    st.rerun()


def mostrar_mensagem(area):
    mensagem = st.session_state.get('mensagem')
    if mensagem and mensagem[0] == area:
        st.success(mensagem[1])
        st.toast('Operação concluída com sucesso.', icon=':material/check_circle:', duration=5)
        del st.session_state['mensagem']


st.caption('OPERAÇÕES  /  INVENTÁRIO')
st.title('Controle de Estoque')
st.caption('Entradas, saídas, reservas e bloqueios por produto.')
st.caption('Sessão temporária · Dados em memória, sem compartilhamento. Recarregar a página ou reiniciar o aplicativo pode apagar o estoque.')
produtos = estoque.listar_produtos()

with st.container(border=True, key='seletor_produto_card'):
    st.subheader('Seu estoque em foco')
    st.caption('Escolha o produto para consultar saldos, movimentar unidades e filtrar o histórico.')
    produto = st.selectbox(
        'Produto para consultar e movimentar', (None, *produtos),
        format_func=lambda codigo: 'Todos os produtos' if codigo is None else codigo,
        key='produto_selecionado',
    )
selecionados = produtos if produto is None else (produto,)
saldos = [estoque.consultar_produto(codigo) for codigo in selecionados]
valores = (
    sum(s.total for s in saldos), sum(s.disponivel for s in saldos),
    sum(s.reservado for s in saldos), sum(s.bloqueado for s in saldos),
)
if produto is None:
    st.caption('Visão geral: quantidades somadas de todos os produtos.')
for coluna, titulo, valor, chave, ajuda in zip(
    st.columns(4), ('Total', 'Disponível', 'Reservado', 'Bloqueado'), valores,
    ('total', 'disponivel', 'reservado', 'bloqueado'),
    ('Unidades no estoque', 'Prontas para utilização', 'Separadas para pedidos', 'Indisponíveis para uso'),
):
    with coluna.container(border=True, key=f'kpi_{chave}'):
        st.metric(titulo, valor)
        st.caption(ajuda)
if produto is None and produtos:
    st.subheader('Estoque por produto')
    st.dataframe([
        {'Produto': s.produto, 'Total': s.total, 'Disponível': s.disponivel,
         'Reservado': s.reservado, 'Bloqueado': s.bloqueado} for s in saldos
    ], hide_index=True, width='stretch')
    st.caption('Valores em unidades. Reservas e bloqueios já estão incluídos no total.')

st.subheader('Operações de estoque')
esquerda, direita = st.columns(2)
with esquerda:
    with st.container(border=True, key='entrada_card'):
        st.subheader('Entrada de unidades')
        mostrar_mensagem('entrada')
        st.caption('Use um código existente ou informe um novo produto.')
        with st.form('entrada', clear_on_submit=True, border=False):
            codigo = st.text_input('Código do produto', key='entrada_produto')
            quantidade = st.number_input('Quantidade de entrada', min_value=1, step=1, key='entrada_quantidade')
            enviar = st.form_submit_button('Registrar entrada', type='primary', width='stretch', key='acao_entrada')
        if enviar:
            try:
                estoque.entrada(codigo, quantidade)
            except ErroEstoque as erro:
                st.error(str(erro))
            else:
                concluir('Entrada registrada com sucesso.', 'entrada')

with direita:
    with st.container(border=True, key='movimento_card'):
        if produto is None:
            st.subheader('Movimentar produto')
            st.info('Selecione um produto acima para realizar saída, reserva ou bloqueio.')
        else:
            st.subheader('Movimentar produto')
            st.caption(f'Produto selecionado: {produto}')
            mostrar_mensagem('movimento')
            operacao = st.radio('Operação', ('Saída', 'Reserva', 'Bloqueio'), horizontal=True, key='operacao')
            with st.form('movimento', clear_on_submit=True, border=False):
                qtd = st.number_input('Quantidade', min_value=1, step=1, key='movimento_quantidade')
                rotulo = 'Solicitação / pedido (obrigatório)' if operacao == 'Reserva' else 'Referência (opcional)'
                referencia = st.text_input(rotulo, key='movimento_referencia', placeholder='Ex.: pedido, solicitação ou documento')
                movimentar = st.form_submit_button('Confirmar operação', type='primary', width='stretch', key='acao_movimento')
            if movimentar:
                try:
                    if operacao == 'Saída':
                        registro = estoque.saida(produto, qtd, referencia)
                        mensagem = f'Saída registrada. ID: {registro.id}'
                    elif operacao == 'Reserva':
                        registro = estoque.reservar(produto, qtd, referencia)
                        mensagem = f'Reserva criada. ID: {registro.id}'
                    else:
                        registro = estoque.bloquear(produto, qtd, referencia)
                        mensagem = f'Bloqueio criado. ID: {registro.id}'
                except ErroEstoque as erro:
                    st.error(str(erro))
                else:
                    concluir(mensagem, 'movimento')


st.subheader('Histórico de operações')
tipo_visualizado = st.selectbox('Operação para visualizar', ('Saída', 'Reserva', 'Bloqueio'), index=1, key='tipo_visualizado')
tipos = {'Saída': 'saida', 'Reserva': 'reserva', 'Bloqueio': 'bloqueio'}
registros = tuple(
    r for codigo in selecionados for r in estoque.listar_registros(codigo)
    if r.tipo == tipos[tipo_visualizado]
)
if registros:
    tabela = pd.DataFrame([
        {'ID': r.id, 'Produto': r.produto, 'Tipo': r.tipo, 'Quantidade': r.quantidade,
         'Referência': r.referencia,
         'Status': 'Concluída' if r.tipo == 'saida' else ('Ativo' if r.ativo else 'Liberado')}
        for r in registros
    ])
    cores_status = {
        'Ativo': 'background-color: #FFF0E5; color: #703000;',
        'Liberado': 'background-color: #E4F3EB; color: #145A38;',
        'Concluída': 'background-color: #E8EDF9; color: #000B40;',
    }
    st.dataframe(
        tabela.style.map(lambda valor: cores_status.get(valor, ''), subset=['Status']),
        hide_index=True, width='stretch',
        column_config={
            'ID': st.column_config.TextColumn('ID', width='large'),
            'Quantidade': st.column_config.NumberColumn('Quantidade', format='%d'),
        },
    )
    st.caption('IDs completos disponíveis na tabela. Se necessário, role horizontalmente ou amplie a tabela.')
else:
    st.info('Nenhum registro deste tipo nesta seleção. Escolha outro tipo ou registre uma operação.')

st.divider()
consulta_coluna, liberacao_coluna = st.columns(2)
with consulta_coluna:
    with st.container(border=True, key='consulta_card'):
        st.subheader('Consultar registro')
        st.caption('Localize uma saída, reserva ou bloqueio de qualquer produto.')
        with st.form('consulta_id', border=False):
            identificador = st.text_input('ID da saída, reserva ou bloqueio', key='consulta_id', placeholder='Cole o ID completo: SAI-…, RES-… ou BLQ-…')
            consultar = st.form_submit_button('Consultar ID', width='stretch')
        if consultar:
            try:
                registro = estoque.consultar_registro(identificador)
            except ErroEstoque as erro:
                st.session_state.pop('registro_consultado', None)
                st.error(str(erro))
            else:
                st.session_state.registro_consultado = registro.id
        if 'registro_consultado' in st.session_state:
            registro = estoque.consultar_registro(st.session_state.registro_consultado)
            status = 'Concluída' if registro.tipo == 'saida' else ('Ativo' if registro.ativo else 'Liberado')
            # HTML apenas para apresentação; todo texto externo é escapado.
            campos = (
                ('Produto', registro.produto),
                ('Operação', {'saida': 'Saída', 'reserva': 'Reserva', 'bloqueio': 'Bloqueio'}[registro.tipo]),
                ('Quantidade', f'{registro.quantidade} unidades'),
                ('Referência', registro.referencia or 'Não informada'),
            )
            detalhes = ''.join(
                f'<div class="consulta-campo"><dt>{escape(rotulo)}</dt><dd>{escape(valor)}</dd></div>'
                for rotulo, valor in campos
            )
            classe_status = 'ativo' if registro.ativo else 'concluido'
            st.html(
                f'<section class="consulta-resultado" aria-label="Detalhes do registro">'
                f'<div class="consulta-cabecalho"><strong>Detalhes do registro</strong>'
                f'<span class="consulta-status {classe_status}">{escape(status)}</span></div>'
                f'<dl class="consulta-grade">{detalhes}</dl></section>'
            )
            st.caption('IDENTIFICADOR DO REGISTRO')
            st.code(registro.id, language=None)
            st.caption('Copie este ID pelo ícone do campo acima.')

with liberacao_coluna:
    with st.container(border=True, key='liberacao_card'):
        st.subheader('Liberar reserva ou bloqueio')
        st.caption('A quantidade completa volta ao disponível. Saídas não podem ser liberadas.')
        mostrar_mensagem('liberacao')
        with st.form('liberacao', clear_on_submit=True, border=False):
            id_liberar = st.text_input('ID para liberar', key='id_liberar', placeholder='Cole o ID completo: RES-… ou BLQ-…')
            liberar = st.form_submit_button('Liberar registro completo', width='stretch')
        if liberar:
            try:
                registro = estoque.liberar(id_liberar)
            except ErroEstoque as erro:
                st.error(str(erro))
            else:
                concluir(f'Registro {registro.id} liberado: {registro.quantidade} unidades disponíveis novamente no produto {registro.produto}.', 'liberacao')
