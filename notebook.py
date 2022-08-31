from dash import dcc, html, callback_context, Dash, page_container, page_registry
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import os, subprocess, re
from datetime import datetime
# pd.options.plotting.backend = "plotly"


# TODO:
# - botao relatório gerar tabela
# - mudar hover_name para cidade e eventos
# - corregir tamanha de frase sobre o card
# CONSERTAR FILTROS QUE NÃO ESTÃO FUNCIONANDO COM EVENTOS (o de ESTADO)


# ============= APP
app = Dash(
    __name__,
    update_title='Carregando...',
    external_stylesheets=[dbc.themes.CYBORG],  # ou SLATE
    use_pages=True,
    title='DashMuseu'
)

server = app.server


if __name__=='__main__':
    app.run_server(debug=True)