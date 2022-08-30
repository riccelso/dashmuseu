from dash import register_page, html, dash_table
from dash.dash_table.Format import Format, Align
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
        'data_inicio', 
        'hora_inicio',
        'hora_fim', 
        'data_fim', 
        'preco', 
        'telefone', 
        'info_para_registro',
        'site', 
        'regiao',
        'nome_museu', 
        'endereco', 
        'cidade', 
        'estado_completo',
        'descricao_longa',
        'descricao_curta', 
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
            columns=[
                {
                    "name": i, 
                    "id": i, 
                    "deletable": True, 
                    'hideable': True,
                    'presentation':'dropdown',
                    # 'format': Format().align(Align.left),
                }

                for i in relatorio.columns
            ],
            row_deletable=True,
            filter_action='native',
            sort_action='native',
            # export_format=True,
            style_as_list_view=True,
            # fixed_rows={'headers': True},
            page_action='none',
            # style_table={
            #     # 'height': '600px', 
            #     'overflowY': 'auto'
            #     },
            style_cell={
                # 'minWidth': 95, 
                # 'maxWidth': 95
                'height':30,
                'textAlign': 'center',
                'textOverflow': 'ellipsis',
                'padding-right': '20px',
                'padding-left': '20px',
                },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '15px',
                'color': 'black',
                'backgroundColor': 'white'
            },
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold',
                'color':'black',
                'textOverflow': 'ellipsis',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(220, 220, 220)',
                },
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "inherit !important",
                    "border": "inherit !important",
                }
            ],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Descricao Curta'},
                    'width': 300, 'minWidth': 300,
                    'maxWidth': 300, 'height': '150%'
                },
                {
                    'if': {'column_id': 'Descricao Longa'},
                    'width': 600, 'minWidth': 600,
                    'maxWidth': 600, 'height': '150%'
                },
                {
                    'if': {'column_id': 'Info Para Registro'},
                    'minWidth': 20,
                    'maxWidth': 600, 'height': '150%'
                },
            ],
            # css=[{
            #     'selector': '.dash-spreadsheet td div',
            #     'rule': '''
            # line-height: 15px;
            # max-height: 30px; min-height: 30px; height: 30px;
            # display: block;
            # overflow-y: hidden;
            # '''
            # }],
            # tooltip_data=[
            #     {
            #         column: {'value': str(value), 'type': 'markdown'}
            #         for column, value in row.items()
            #     } for row in relatorio.to_dict('records')
            # ],
            # tooltip_duration=None,
            # virtualization=True,
            #deletable=True,
            # selectable=True,
            # filter_options={'case':'insensitive'}
        )
    ])

    return layout