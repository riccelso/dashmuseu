from dash import register_page, html, dash_table
from .tabelas import (
    pd,
    eventos,
    occ,
    museu,
    museu2,
    faixaetaria,
    libras,
    regiao,
    estados,
    inter,
    np
)
import os #EXCLUIR

register_page(
    __name__, 
    path_template="/relatorio",
    update_title='Carregando...',
    title='DashMuseu - Relatório de eventos',
    )


def layout(
    mes_inicio_param=None,
    mes_fim_param=None,
    ano_param=None,
    ano_fim_param=None,
    faixaetaria_param=None,
    libras_param=None,
    estado_param=None,
    **kwargs
    ):

    os.system('cls')
    pd.set_option('display.max_columns', None)

    occ_temp = occ[['id_occ', 'eventId', 'spaceId', 'data_inicio', 'hora_inicio', 'hora_fim', 'data_fim', 'timezone', 'preco']]

    event_temp = eventos[['id_eventos', 'nome', 'faixa_etaria', 'descricao_longa',
                          'descricao_curta', 'telefone', 'traducao_libras', 'info_para_registro',
                          'site']]

    event_temp.rename(dict(nome='nome_evento'), axis=1, inplace=True)

    museu_temp = museu2[['id_museu', 'regiao', 'nome', 'endereco',
                  'cidade', 'estado_completo']].copy()

    museu_temp.rename({'nome':'nome_museu'}, axis=1, inplace=True)

    relatorio = pd.merge(
        occ_temp, 
        museu_temp, 
        left_on='spaceId', 
        right_on='id_museu',
        how='left'
    )
    
    relatorio = pd.merge(
        event_temp, 
        relatorio, 
        left_on='id_eventos',
        right_on='eventId',
        how='right'
    )


    relatorio = relatorio[[
        'nome_evento', 
        'faixa_etaria', 
        'traducao_libras', 
        'descricao_longa',
        'descricao_curta', 
        'telefone', 
        'info_para_registro',
        'site', 
        'data_inicio', 
        'hora_inicio',
        'hora_fim', 
        'data_fim', 
        'preco', 
        'regiao',
        'nome_museu', 
        'endereco', 
        'cidade', 
        'estado_completo'
        ]].copy()  # CORRIGIR 'timezone' NO DATABRICKS
    
    relatorio['faixa_etaria'] = relatorio.faixa_etaria.replace(
        dict(faixaetaria.values)).copy()
    
    relatorio['traducao_libras'] = relatorio.traducao_libras.replace(
        dict(libras.values)).copy()

    relatorio['estado_completo'] = relatorio['estado_completo'].replace(
        dict(estados[['id_estados', 'estado']].values)).copy()

    relatorio['regiao'] = relatorio.regiao.replace(dict(regiao.values))
    

    if not faixaetaria_param is None:
        relatorio = relatorio[relatorio.faixa_etaria == faixaetaria_param]

    if not libras_param is None:
        relatorio = relatorio[relatorio.traducao_libras == libras_param]

    relatorio['data_inicio'] = relatorio.data_inicio.astype(np.datetime64)
    relatorio['data_fim'] = relatorio.data_fim.astype(np.datetime64)

    if mes_inicio_param and mes_fim_param is None:
        relatorio = relatorio[relatorio.data_inicio.dt.month == int(mes_inicio_param)]

    elif mes_inicio_param and mes_fim_param:
        relatorio = relatorio[relatorio.data_inicio.dt.month >= int(mes_inicio_param)]
        relatorio = relatorio[relatorio.data_fim.dt.month <= int(mes_fim_param)]

    if estado_param:
        relatorio = relatorio[relatorio.estado_completo == estado_param]

    relatorio.columns = [col.replace('_', ' ').title()
                         for col in relatorio.columns]

    layout = html.Div([
        dash_table.DataTable(
            data=relatorio.to_dict('records'),
            columns=[{"name": i, "id": i} for i in relatorio.columns],
        )
    ])

    return layout