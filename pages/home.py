import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, callback_context, register_page, page_container, page_registry, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np
import os
import subprocess
import re
from datetime import datetime

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


inicio = inter.data_inicio.min()
fim = inter.data_inicio.max()

cor_eventos = px.colors.sequential.Blues[3:]
cor_museus = 'Viridis'

# CARDS E METRICAS:
cards_e_metricas = \
    {
        'Localização dos museus': {
            'card1': {
                'titulo': '**Total de museus**',
                'img': 'soma_total.png'
            },
            'card2': {
                'titulo': '**Região c/ mais museus**',
                'img': 'evento.png'
            },
            'card3': {
                'titulo': '**Cidade c/ mais museus**',
                'img': 'mapa-da-cidade.png'
            }
        },
        'Eventos por museu': {
            'card1': {
                'titulo': '**Total de eventos**',
                'img': 'calendario.png'
            },
            'card2': {
                'titulo': '**Museu c/ mais eventos**',
                'img': 'museu_card.png'
            },
            'card3': {
                'titulo': '**Cidade c/ mais eventos**',
                'img': 'mapa-da-cidade.png'
            }
        },
    }

# VARIÁVEIS AUXILIARES

cor_cards = '#08336F'
espaco_inter_col = '10px'
dist_labdrops = '15px'
teto = '10px'

result_config = {
    'font-size': '22px',
    'text-align': 'center',
    'position': 'relative',
    'margin-left': '8px',
    'line-height': '1.2',
}

drop_styles = \
    {
        'margin': 'auto',
        'margin-top': '2px',
        'font-size': '100%',
        'width': '297px'
    }

cards_config = {
    # 'border-color': 'white',
    'height': '87px',
    'width': 'auto',
}

# ============= MONTAGEM DE COMPONENTES
# COLUNA 1


logo = html.Img(
    id='logo',
    src='assets/proc_museus.png',
    style={
        'height': '80px',
        'width': '220px',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'margin-top': '5px',
    }
)

card1 = [
    dbc.Row([
        dbc.Col([
            html.Img(
                id='card1',
                src='assets/soma_total.png',
                style={
                    'height': '50px',
                    'width': '55px',
                    'margin-left': '15px',
                    'margin-top': '20px',
                }
            ),
        ], sm=3),
        dbc.Col([
            dcc.Markdown(children=['**Total de museus**'],
                         style={'font-size': '16px', 'text-align': 'center'},
                         id='titulo1'),
            dcc.Markdown(children=[''],
                         id='resultado1',
                         style=result_config,
                         ),
        ], style={
            'margin-top': '2px',
            'margin-right': '20px',
        }),
    ]),
]

card2 = [
    dbc.Row([
        dbc.Col([
            html.Img(
                id='card2',
                src='assets/evento.png',
                style={
                    'height': '50px',
                    'width': '55px',
                    'margin-left': '15px',
                    'margin-top': '20px',
                }
            ),
        ], sm=3),
        dbc.Col([
            dcc.Markdown(children=['**Região c/ mais museus**'],
                         style={'font-size': '16px', 'text-align': 'center'},
                         id='titulo2'),
            dcc.Markdown(children=[''],
                         id='resultado2',
                         style=result_config,
                         ),
        ], style={
            'margin-top': '2px',
            'margin-right': '20px',
        }),
    ]),
]

card3 = [
    dbc.Row([
        dbc.Col([
            html.Img(
                id='card3',
                src='assets/evento.png',
                style={
                    'height': '50px',
                    'width': '55px',
                    'margin-left': '15px',
                    'margin-top': '20px',
                }
            ),
        ], sm=3),
        dbc.Col([
            dcc.Markdown(children=['**Cidade c/ mais museus**'],
                         style={'font-size': '16px', 'text-align': 'center'},
                         id='titulo3'),
            dcc.Markdown(children=[''],
                         id='resultado3',
                         style=result_config,
                         ),
        ], style={
            'margin-top': '2px',
            'margin-right': '20px',
        }),
    ]),
]

drop1 = dcc.Dropdown(
    options=[{'label': i, 'value': i}
             for i in sorted(faixaetaria.faixa_etaria.unique())],
    id='drop_idade',
    placeholder='Habilitado somente para os eventos',
    disabled=True,
)


drop2 = dcc.Dropdown(
    options=[{'label': i, 'value': i}
             for i in libras.trad_libras.unique()[::-1]],
    id='assistencia',
    placeholder='Habilitado somente para os eventos',
    disabled=True,
)

drop3 = dcc.Dropdown(
    options=[{'label': i, 'value': i}
             for i in estados.estado.values],  # COLOCAR ESTADOS
    id='estados',
    placeholder='Clique para selecionar',
    # multi=True,
    #value='BAHIA'
)


check = dcc.RadioItems(
    id='check',
    options=[
        {
            'label': i,
            'value': i
        }
        for i in [' Eventos por museu', ' Localização dos museus']
    ],
    value=' Localização dos museus',
)

buttons = dbc.Col([
    dbc.Button(
        'Resetar filtros',
        id='btn1',
        color="secondary",
        size="sm",
        style={
            'margin-left': '15px',
            # 'margin-bottom':'20px',
            'margin-top': '10px',
            'width': '120px'
        }
    ),
    dbc.Button(
        'Relatório de eventos',
        id='btn2',
        color="secondary",
        size="sm",
        style={
            'margin-left': '15px',
            # 'margin-bottom':'20px',
            'margin-top': '10px',
            'width': '145px'
        },
        disabled=True,
        href="/relatorio"
    ),
])

date_range = dbc.Row([
    dbc.Row([
        dbc.Col([
            html.Label('Mês de inicio',
                style={'font-size': '11px', 'color': 'white'}),
            dcc.Dropdown(
                options=[{'label': i, 'value': i}
                         for i in range(1, 12+1)],
                id='mes_inicio',
                placeholder='Inicio',
                disabled=True,
                style={'width': '70px'}
            )
        ], style={'margin-left': '10px'}),
        dbc.Col([
            html.Label('Mês de fim',
                style={'font-size': '11px', 'color': 'white'}),
            dcc.Dropdown(
                id='mes_fim',
                placeholder='Fim',
                style={'width': '70px'},
                disabled=True,
            )
        ]),
    ], style={'color': 'black'}),
    dbc.Row([
        dbc.Col([
            html.Label('Ano de inicio',
                style={'font-size': '11px', 'color': 'white'}),
            dcc.Dropdown(
                options=[{'label': i, 'value': i}
                         for i in range(inicio.year, fim.year+1)],
                id='ano',
                placeholder='Inicio',
                disabled=True,
            )
        ], style={'width': '85px', 'margin-left': '10px'}),
        dbc.Col([
            html.Label('Ano de fim',
                style={'font-size': '11px', 'color': 'white'}),
            dcc.Dropdown(
                id='ano_fim',
                placeholder='Fim',
                disabled=True,
            )
        ], style={'width': '85px', 'margin-left': '10px'})
    ], style={'color': 'black'})
])

# date_range = dbc.Col([
#     html.Div(
#         [
#             dcc.RangeSlider(
#                 id="mes",
#                 min=1,
#                 max=12,
#                 step=1,
#                 marks={
#                     str(i): ''  # str(i)[2:]
#                     for i in range(1, 12 + 1)
#                 },
#                 tooltip={"placement": "bottom", "always_visible": True}
#             ),
#         ],
#     ),
#     html.Div([
#         dcc.RangeSlider(
#             id="ano",
#             min=inicio.year,
#             max=fim.year,
#             step=1,
#             marks=\
#                 {
#                     str(i): ''# str(i)[2:]
#                     for i in range(inicio.year, fim.year +1)
#                 },
#             tooltip={"placement": "bottom", "always_visible": True}
#         ),
#     ])
# ])

# date_range = dcc.DatePickerRange(
#     id='date_range',
#     min_date_allowed=inicio,
#     max_date_allowed=fim,
#     start_date=inicio,
#     end_date=fim,
#     display_format='DD/MM/YYYY',
#     disabled=True,
# )


# COLUNA 2
mapa = dcc.Graph(id='mapa')


fig = go.Figure()
fig.update_layout(
    template='plotly_dark',
    paper_bgcolor=('rgba(0, 0, 0, 0)'),
    margin={'l': 2, 'r': 0, 't': 1, 'b': 2},
    showlegend=False
)

# ============= LAYOUT

register_page(
    __name__,
    path_template="/",
    title='DashMuseu - Página inicial',
)




layout = html.Div([
    dbc.Row([
        dbc.Col([  # COLUNA 1

                html.Div([
                    dbc.Card(
                        logo,
                        color=cor_cards,
                        inverse=True,
                        style={'margin-top': teto}
                    ),
                ]),  # style={'margin-right': '50px'}
                # color='primary',
            dbc.Card([
                html.Div([

                    html.Div([
                        dbc.Row([
                            html.Label('Filtros de data:', style={
                                'margin-bottom': '-8px'}),
                            date_range,
                        ])
                    ]),

                    html.Div([
                        # CAIXA 1
                        html.Label(children=['Filtro de faixa etária:'], id='l1', style={
                            'margin-top': '10px'}),

                        # DROPDOWN 1
                        dbc.Col([drop1], style={
                            'margin-bottom': dist_labdrops,
                            'padding-right': '11px',
                            'color': 'black',
                        }),

                        # CAIXA 2
                        html.Label(
                            children=['Interprete de Libras:'], id='l2'),
                        # DROPDOWN 2
                        dbc.Col([drop2], style={
                            'margin-bottom': dist_labdrops,
                            'padding-right': '11px',
                            'color': 'black',
                        }),

                        html.Label(children=['Filtro por Estado:'],
                                   id='l3'),  # CAIXA 3
                        # DROPDOWN 3
                        dbc.Col([drop3], style={
                            'margin-bottom': dist_labdrops,
                            'padding-right': '11px',
                            'color': 'black',
                        }),
                    ], style={'margin-bottom': '4px'}),

                    # CAIXA 4
                    html.Label(children=['Tipos de visualização:'], id='l4'),
                    dbc.Row([check, buttons], style={'margin-top': '1px'}),
                ], style=drop_styles),
            ],
                    color='secondary',
                    inverse=True,
                    outline=True,
                    style={
                # 'width':'316px',
                'height': '79vh',
                'margin-top': '35px',
            }
                    )

        ],
            style={'width': 'auto'}),  # sm=3),

        html.Div([
            dbc.Col([  # COLUNA 2

                dbc.Row([
                    dbc.Col([
                        dbc.Card(
                            card1,
                            color=cor_cards,
                            inverse=True,
                            outline=True,
                            className='cards',
                            style=cards_config
                        ),
                    ]),
                    dbc.Col([
                        dbc.Card(
                            card2,
                            color=cor_cards,
                            inverse=True,
                            className='cards',
                            style=cards_config
                        ),
                    ]),
                    dbc.Col([
                        dbc.Card(
                            card3,
                            color=cor_cards,
                            inverse=True,
                            className='cards',
                            style=cards_config
                        ),
                    ])
                ], style={
                    'margin-top': teto,
                    'margin-left': '12px'
                }),

                dbc.Row([mapa], style={
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                    'margin-left': espaco_inter_col,
                    'height': '82vh',
                    'width': '100%'
                }
                )  # C2 L2

            ]), ], style={'width': '938px'})
    ]),
], style={
    'margin': '30px',
    'margin-top': '0px',
    'flex-direction': 'col',
    # 'font-family': 'Sans-serif',
})


@callback(
    Output('drop_idade', 'value'),
    Output('assistencia', 'value'),
    Output('estados', 'value'),
    Output('mes_inicio', 'value'),
    Output('mes_fim', 'value'),
    Output('ano', 'value'),
    Output('ano_fim', 'value'),
    Input('btn1', 'n_clicks'),
)
def limpar_filtros(btn1):
    return None, None, None, None, None, None, None


@callback(
    Output('mapa', 'figure'),
    Output('drop_idade', 'placeholder'),
    Output('assistencia', 'placeholder'),
    Output('assistencia', 'disabled'),
    Output('drop_idade', 'disabled'),
    Output('resultado1', 'children'),
    Output('resultado2', 'children'),
    Output('resultado3', 'children'),
    Output('resultado1', 'style'),
    Output('resultado2', 'style'),
    Output('resultado3', 'style'),
    Input('mes_inicio', 'value'),
    Input('mes_fim', 'value'),
    Input('ano', 'value'),
    Input('ano_fim', 'value'),
    Input('resultado1', 'style'),
    Input('resultado2', 'style'),
    Input('resultado3', 'style'),
    Input('drop_idade', 'value'),
    Input('assistencia', 'value'),
    Input('estados', 'value'),
    Input('btn1', 'n_clicks'),
    Input('check', 'value')
)
def config_dados(mes_inicio, mes_fim, ano_inicio, ano_fim, style1, style2, style3, drop_idade, drop_assistencia, drop_estado, btn1, check):
    # Verificando ação de reset
    reset = callback_context.triggered[0]['prop_id'] == 'btn1.n_clicks'
    styles = [style1, style2, style3]

    # Tratamento de variáveis
    check = check.strip()

    if check == 'Eventos por museu':
        placeholder = 'Clique para selecionar'
        disabled = False
    else:
        placeholder = 'Habilitado somente para os eventos'
        disabled = True

    # Filtrando dataframe
    temp = inter.copy()

    if not drop_idade is None and not reset:
        temp = temp[temp.faixa_etaria == drop_idade]

    if not drop_assistencia is None and not reset:
        temp = temp[temp.traducao_libras == drop_assistencia]

    if ano_inicio and ano_fim is None:
        temp = temp[temp.data_inicio.dt.year == ano_inicio]
    elif ano_inicio and ano_fim:
        temp = temp[temp.data_inicio.dt.year >= ano_inicio]
        temp = temp[temp.data_inicio.dt.year <= ano_fim]

    if mes_inicio and mes_fim is None:
        temp = temp[temp.data_inicio.dt.month == mes_inicio]
    elif mes_inicio and mes_fim:
        temp = temp[temp.data_inicio.dt.month >= mes_inicio]
        temp = temp[temp.data_inicio.dt.month <= mes_fim]

    # if len(data_inicio) <= 10:
    #     data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
    #     data_inicio = temp['data_inicio'] >= data_inicio
    #     temp = temp[(data_inicio)]
    # if len(data_fim) <= 10:
    #     data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
    #     data_fim = temp['data_fim'] <= data_fim
    #     temp = temp[(data_fim)]

    if temp.empty:
        contagem_museus = ''
        regiao_com_mais_museus = ''
        cidades_com_mais_museus = ''
        contagem_eventos = ''
        museu_mais_eventos = ''
        cidade_mais_eventos = ''
    print(temp.columns)

    if check == 'Eventos por museu':
        contagem_eventos = str(np.count_nonzero(temp.id_eventos.unique()))

        museu_mais_eventos = temp[['nome_y', 'id_eventos']].groupby(
            'nome_y').count()
        museu_mais_eventos = museu_mais_eventos.nlargest(
            1, 'id_eventos')

        if museu_mais_eventos.empty:
            museu_mais_eventos = ''
        else:
            museu_mais_eventos = museu_mais_eventos.index[0]
            if 'bonde da história' in museu_mais_eventos.lower():
                museu_mais_eventos = 'Bonde da História'

        cidade_mais_eventos = pd.merge(
            museu[['id_museu', 'cidade']],
            temp[['id_museu', 'id_eventos']],
            on='id_museu',
            how='left'
        )[['cidade', 'id_eventos']]

        cidade_mais_eventos = cidade_mais_eventos.groupby('cidade').count()
        cidade_mais_eventos = cidade_mais_eventos.nlargest(
            1, 'id_eventos')

        if cidade_mais_eventos.empty:
            cidade_mais_eventos = ''
        elif cidade_mais_eventos.values.flatten()[0] == 0:
            cidade_mais_eventos = ''
        else:
            cidade_mais_eventos = cidade_mais_eventos.index[0]

    temp = temp[['id_museu', 'eventId']].groupby(
        'id_museu', as_index=None).count()
    temp.rename(columns={'eventId': 'contagem_eventos'}, inplace=True)

    temp = pd.merge(
        museu,
        temp,
        on='id_museu',
        how='left'
    )

    # temp = temp[[
    #     'latitude',
    #     'longitude',
    #     'endereco',
    #     'cidade',
    #     'regiao',
    #     'contagem_eventos',
    #     'sigla_estado',
    #     'estado_completo',
    #     'cidade',
    #     ]]

    temp['estado_completo'] = temp['estado_completo'].replace(
        dict(estados[['id_estados', 'estado']].values)).copy()

    temp['sigla_estado'] = temp['sigla_estado'].replace(
        dict(estados[['id_estados', 'sigla']].values)).copy()

    if not drop_estado is None and not reset:
        temp = temp[temp.estado_completo == drop_estado]

    if check == 'Eventos por museu':
        temp = temp[temp.contagem_eventos.fillna(0) > 0]

    temp['regiao'] = temp.regiao.replace(dict(regiao.values))
    temp['regiao'] = temp.regiao.astype("category")

    # CARDS E METRICAS:

    if temp.empty:
        contagem_museus = ''
        regiao_com_mais_museus = ''
        cidades_com_mais_museus = ''
    elif check == 'Localização dos museus':
        contagem_museus = str(np.count_nonzero(temp.id_museu.unique()))

        regiao_com_mais_museus = temp[[
            'id_museu', 'regiao']].groupby('regiao').count()
        regiao_com_mais_museus = regiao_com_mais_museus.nlargest(1, 'id_museu')

        if regiao_com_mais_museus.empty:
            regiao_com_mais_museus = ''
        else:
            regiao_com_mais_museus = regiao_com_mais_museus.index[0]

        #cidades_com_mais_museus = temp
        cidades_com_mais_museus = temp[[
            'cidade',
            'id_museu'
        ]].groupby('cidade').count()

        cidades_com_mais_museus = cidades_com_mais_museus.nlargest(
            1,
            'id_museu'
        )

        if cidades_com_mais_museus.empty:
            cidades_com_mais_museus = ''
        else:
            cidades_com_mais_museus = cidades_com_mais_museus.index[0]

    # AUTENTICANDO MAPBOX
    px.set_mapbox_access_token(open('mapbox/mapbox', 'r').read())

    # CENTRALIZANDO MAPBOX
    if temp.empty:
        zoom, centro = 3.35, dict(lat=-13.904, lon=-49.747)
    else:
        if check == 'Localização dos museus':
            centro = dict(
                lat=temp.latitude.mean()+3.5,
                lon=temp.longitude.mean()
            )\
                if drop_estado is None else \
                dict(
                lat=temp.latitude.mean(),
                lon=temp.longitude.mean()
            )

            zoom = 3 if drop_estado is None else 5
        elif check == 'Eventos por museu':
            centro = dict(lat=temp.latitude.mean(),
                          lon=temp.longitude.mean())
            zoom = 3.2 if drop_estado is None else 6

    # DEFININDO MAPA
    cor = cor_eventos if check == 'Eventos por museu' else cor_museus

    fig_1 = px.scatter_mapbox(
        temp,
        lat='latitude',
        lon='longitude',
        zoom=zoom,
        color='regiao' if check == 'Localização dos museus' else 'contagem_eventos',
        # color_discrete_sequence=cor,
        color_continuous_scale=cor,
        # color_discrete_map=cor,
        size='contagem_eventos' if check == 'Eventos por museu' else None,
        size_max=30
    )

    fig_1.update_layout(
        # outra maneira -> lat=-16.6, lon=-50.6)),
        mapbox=dict(center=go.layout.mapbox.Center(centro)),
        template='plotly_dark',  # plotly_dark
        paper_bgcolor=('rgba(0, 0, 0, 0)'),
        # ou margin=go.layout.Margin(l=2, r=0, t=10, b=2)
        margin={'l': 2, 'r': 0, 't': 10, 'b': 2},
        showlegend=True,  # adicionar opção de ver legenda
        legend=dict(
            orientation="h",
            #bgcolor="Grey",
            yanchor="top",
            y=1.05,
            xanchor="left",
            x=0,
            title='Regiões',
            # title_font_family="Times New Roman",
        ))

    fig_1.update_coloraxes(showscale=True)
    fig_1.layout.coloraxis.colorbar.title = 'Eventos'

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        )
    )

    #hover_name = "country",
    # hover_data = ["continent", "pop"]

    # hovertemplate =
    # '<i>Price</i>: $%{y:.2f}'+
    # '<br><b>X</b>: %{x}<br>'+
    # '<b>%{text}</b>',

    # hovertemplate="%{label}: <br>Popularity: %{percent} </br> %{text}"

    if not check == 'Eventos por museu':
        resultados = [[contagem_museus],
                      [regiao_com_mais_museus.title()],
                      [cidades_com_mais_museus]]

        for i, resp in enumerate(resultados):
            if len(resp[0]) > 17 and ' ' in resp[0]:
                styles[i].update({'margin-top': '-12px'})
            else:
                styles[i].update({'margin-top': '0px'})

    else:
        resultados = [[contagem_eventos],
                      [museu_mais_eventos],
                      [cidade_mais_eventos]]

        for i, resp in enumerate(resultados):
            padrao = re.search('[:"-]', resp[0])
            if padrao:
                resultados[i] = [resp[0][:padrao.span()[0]]]

            if len(resp[0]) > 17 and ' ' in resp[0]:
                styles[i].update({'margin-top': '-12px'})
            else:
                styles[i].update({'margin-top': '0px'})

    return (
        fig_1,
        placeholder,
        placeholder,
        disabled,
        disabled,
        *resultados,
        *styles,
    )


@callback(
    Output('estados', 'options'),
    Input('check', 'value')
)
def mudar_opcoes(check):
    check = check.strip()
    temp = inter.copy()
    temp = temp[['id_museu', 'eventId']].groupby(
        'id_museu', as_index=None).count()
    temp.rename(columns={'eventId': 'contagem_eventos'}, inplace=True)

    temp = pd.merge(
        museu,
        temp,
        on='id_museu',
        how='left'
    )[['contagem_eventos', 'estado_completo']]

    temp.fillna(0, inplace=True)

    temp['estado_completo'] = temp['estado_completo'].replace(
        dict(estados[['id_estados', 'estado']].values)).copy()

    if check == 'Eventos por museu':
        return [{'label': i, 'value': i} for i in np.unique(temp[temp.contagem_eventos > 0].estado_completo.values)]
    return [{'label': i, 'value': i} for i in estados.estado.values]


@callback(
    Output('titulo1', 'children'),
    Output('titulo2', 'children'),
    Output('titulo3', 'children'),
    Output('card1', 'src'),
    Output('card2', 'src'),
    Output('card3', 'src'),
    Input('check', 'value'),
)
def cabecalho_cards(check):
    check = check.strip()
    infos = cards_e_metricas[check]

    imagens = []
    for info in ['card1', 'card2', 'card3']:
        imagens.append(f"assets/{infos[info]['img']}")

    return infos['card1']['titulo'], infos['card2']['titulo'], infos['card3']['titulo'], *imagens


@callback(
    Output('mes_inicio', 'disabled'),
    Output('ano', 'disabled'),
    Output('btn2', 'disabled'),
    Input('check', 'value'),
)
def filtro_de_datas(check):
    if check == ' Eventos por museu':
        return False, False, False
    return True, True, True


@callback(
    Output('mes_fim', 'disabled'),
    Output('mes_fim', 'options'),
    Input('mes_inicio', 'value'),
)
def mes_fim(data_inicio):
    if data_inicio == 12 or data_inicio is None:
        return True, []

    options = [{'label': i, 'value': i} for i in range(data_inicio, 12+1)]

    return False, options


@callback(
    Output('ano_fim', 'disabled'),
    Output('ano_fim', 'options'),
    Input('ano', 'value'),
)
def ano_fim(ano_inicio):

    if ano_inicio == fim.year or ano_inicio is None:
        return True, []

    options = [{'label': i, 'value': i}
               for i in range(ano_inicio, fim.year+1)]

    return False, options


@callback(
    Output('btn2', 'href'),
    Input('mes_inicio', 'value'),
    Input('mes_fim', 'value'),
    Input('ano', 'value'),
    Input('ano_fim', 'value'),
    Input('drop_idade', 'value'),
    Input('assistencia', 'value'),
    Input('estados', 'value'),
)
def link_para_tabela(mes_inicio, mes_fim, ano, ano_fim, faixaetaria, libras, estados):
    query_filtros = []

    if mes_inicio and mes_fim is None:
        query_filtros.append(f'mes_inicio_param={mes_inicio}')
    elif mes_inicio and mes_fim:
        query_filtros.append(f'mes_inicio_param={mes_inicio}')
        query_filtros.append(f'mes_fim_param={mes_fim}')

    if ano and ano_fim is None:
        query_filtros.append(f'ano_param={ano}')
    elif ano and ano_fim:
        query_filtros.append(f'ano_param={ano}')
        query_filtros.append(f'ano_fim_param={ano_fim}')

    if faixaetaria:
        query_filtros.append(f'faixaetaria_param={faixaetaria}')

    if libras:
        query_filtros.append(f'libras_param={libras}')
        
    if estados:
        query_filtros.append(f'estados_param={estados}')

    if len(query_filtros) > 0:
        result = 'relatorio?' + '&'.join(query_filtros)
        return result
    else:
        return 'relatorio'