from dash import dcc, html, callback_context, Dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import os, subprocess
import gunicorn

# pd.options.plotting.backend = "plotly"

eventos = pd.read_parquet("curated/eventos")
occ = pd.read_parquet('curated/ocorrencias')
museu = pd.read_parquet('curated/museu')
faixaetaria = pd.read_parquet("curated/faixaetaria")
libras = pd.read_parquet("curated/libras")
regiao = pd.read_parquet('curated/regiao')
estados = pd.read_parquet('curated/estados')



museu2 = museu[['id_museu', 'regiao', 'latitude', 'longitude']]
inter = pd.merge(
    museu2, 
    occ[['spaceId', 'eventId']], 
    left_on='id_museu', 
    right_on='spaceId', 
    how='right'
)

inter = pd.merge(
    inter,
    eventos,
    left_on='eventId',
    right_on='id_eventos',
    how='left'
)

inter['faixa_etaria'] = inter.faixa_etaria.replace(
    dict(faixaetaria.values)).copy()
inter['traducao_libras'] = inter.traducao_libras.replace(
    dict(libras.values)).copy()


cor_eventos = px.colors.sequential.Blues[3:]

#px.colors.sequential.swatches()




# TODO:
# - mudar font
# - mudar hover_name para cidade e eventos
# - serie temporal acima do mapa
# - deseparecer com opções se a escolha for "localização dos museus"?
# - colocar legenda dentro de quadradro/card ou dentro do gráfico
# - colocar filtros dentro de quadradro/card
# - modificar logo
# - mudar botao "resetar filtros"
# - Cards com totais:
#    nº total de eventos, total de museus, estado com + museus, museus com + eventos
# - abaixar slider

# ============= APP
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
server = app.server

# ============= MONTAGEM DE COMPONENTES
# COLUNA 1

logo = html.Img(
    id='logo',
    src=app.get_asset_url('corn.png'),
    style={'height': '50px', 'width': '80px', 'margin-left': '60px',
           'margin-bottom': '20px', 'margin-top': '10px'}
)  # width = largura

drop1 = dcc.Dropdown(
    options=[{'label': i, 'value': i}
             for i in sorted(faixaetaria.faixa_etaria.unique())],
    id='drop_idade',
    placeholder='Clique para selecionar',
    #value='18 anos'
)

drop2 = dcc.Dropdown(
    options=[{'label': i, 'value': i}
             for i in libras.trad_libras.unique()[-1:0:-1]],
    id='assistencia',
    placeholder='Clique para selecionar',
    #value='Sim'
)

drop3 = dcc.Dropdown(
    options=[{'label': i, 'value': i}
             for i in estados.estado.values],  # COLOCAR ESTADOS
    id='estados',
    placeholder='Clique para selecionar',
    #multi=True
    #value='BAHIA'
)


check = dcc.RadioItems(
    id='check',
    options=[
        {'label': i, 'value': i}
        for i in ['Eventos por museu', 'Localização dos museus']
    ],
    value='Localização dos museus',
)

bt1 = dbc.Button('Resetar filtros', id='btn1', color="secondary",
                 size="sm", style={'margin-left': '0px'})

slicer = dcc.Slider(
    min=0,
    max=10,
    step=2.5,
    value=10,
    id='my-slider',
    marks={
        0: '0°F',
        2.5: '2.5°F',
        5: '5°F',
        7.5: '7.5°F',
        10: {'label': '10°F', 'style': {'color': '#f50'}}
    },
)

# COLUNA 2
mapa = dcc.Graph(id='mapa')


fig = go.Figure()
fig.update_layout(
    template='plotly_dark',
    paper_bgcolor=('rgba(0, 0, 0, 0)'),
    margin={'l': 2, 'r': 0, 't': 1, 'b': 2},
    showlegend=False
)

# slicer = dcc.Graph(id='slicer', figure=fig)

# VARIÁVEIS AUXILIARES

dist_labdrops = '15px'



# ============= LAYOUT

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([  # COLUNA 1
            dbc.Row([logo], style={'margin-top': '30px'}),

            html.Div([
                # CAIXA 1
                html.Label(children=['Filtro de faixa etária:'], id='l1'),
                # DROPDOWN 1
                dbc.Col([drop1], style={'margin-bottom': dist_labdrops}),

                # CAIXA 2
                html.Label(children=['Interprete de Libras:'], id='l2'),
                # DROPDOWN 2
                dbc.Col([drop2], style={'margin-bottom': dist_labdrops}),

                html.Label(children=['Filtro por Estado:'],
                           id='l3'),  # CAIXA 3
                # DROPDOWN 3
                dbc.Col([drop3], style={'margin-bottom': dist_labdrops}),

                html.Label(children=['Tipos de visualização:'], id='l4', style={
                           'margin-top': '15px'}),  # CAIXA 4
                dbc.Row([check], style={'margin-top': '1px'}),
            ], style={'margin-top': '50px'}),
            html.Div(bt1, style={'margin-top': '32px'}),

        ], sm=3),

        dbc.Col([  # COLUNA 2

            dbc.Row([slicer], style={'height': '10vh',
                    'margin-top': '50px'}),  # C2 L1
            dbc.Row([mapa], style={
                    'margin-top': '20px', 'margin-right': '1px', 'height': '75vh'})  # C2 L2

        ], sm=9),
    ])
])


@app.callback(
    Output('drop_idade', 'value'),
    Output('assistencia', 'value'),
    Output('estados', 'value'),
    Input('btn1', 'n_clicks'),
)
def limpar_filtros(btn1):
    return None, None, None


@app.callback(
    Output('mapa', 'figure'),
    Input('drop_idade', 'value'),
    Input('assistencia', 'value'),
    Input('estados', 'value'),
    Input('btn1', 'n_clicks'),
    Input('check', 'value')
)
def ver_resultado(drop_idade, drop_assistencia, drop_estado, btn1, check):
    global last_lon, last_lat

    # filtrando dataframe
    temp = inter.copy()
    reset = callback_context.triggered[0]['prop_id'] == 'btn1.n_clicks'

    if not drop_idade is None and not reset:
        temp = temp[temp.faixa_etaria == drop_idade]

    if not drop_assistencia is None and not reset:
        temp = temp[temp.traducao_libras == drop_assistencia]

    temp = temp[['id_museu', 'eventId']].groupby(
        'id_museu', as_index=None).count()
    temp.rename(columns={'eventId': 'contagem_eventos'}, inplace=True)

    temp = pd.merge(
        museu,
        temp,
        on='id_museu',
        how='left'
    )[['latitude', 'longitude', 'regiao', 'contagem_eventos', 'estado_completo']]

    temp['estado_completo'] = temp['estado_completo'].replace(
        dict(estados[['id_estados', 'estado']].values)).copy()

    if not drop_estado is None and not reset:
        temp = temp[temp.estado_completo == drop_estado]

    if check == 'Eventos por museu':
        temp = temp[temp.contagem_eventos > 0]

        
    temp['regiao'] = temp.regiao.replace(dict(regiao.values))
    temp['regiao'] = temp.regiao.astype("category")

    # AUTENTICANDO MAPBOX
    px.set_mapbox_access_token(open('mapbox/mapbox', 'r').read())

    # CENTRALIZANDO MAPBOX
    if temp.empty:
        zoom, centro = 3.35, dict(lat=-13.904, lon=-49.747)
    else:
        if check == 'Localização dos museus':
            centro = dict(lat=temp.latitude.mean()+2.3,
                          lon=temp.longitude.mean())
            zoom = 3 if drop_estado is None else 4
        elif check == 'Eventos por museu':
            centro = dict(lat=temp.latitude.mean()+4,
                          lon=temp.longitude.mean())
            zoom = 3.2 if drop_estado is None else 4

    # DEFININDO MAPA
    cor = cor_eventos if check == 'Eventos por museu' else 'Viridis'

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
            title='Região',
            # title_font_family="Times New Roman",
        ))

    fig_1.update_coloraxes(showscale=True)
    fig_1.layout.coloraxis.colorbar.title = 'Eventos'

    # fig_1.update(layout_coloraxis_showscale=False)
    # fig_1.layout.coloraxis.showscale = False
    #fig_1.update_traces(marker_showscale=False)
    #fig_1.update_layout(mapbox_style='mapbox://styles/ricelsos/cl756fj5w001814n2bz85vj3h')

    return fig_1


@app.callback(
    Output('estados', 'options'),
    Input('check', 'value')
)
def mudar_opcoes(check):
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

port = os.getenv('PORT')


app.run_server(
    port=port,
)
