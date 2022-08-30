import pandas as pd
import numpy as np

eventos = pd.read_parquet("curated/eventos")
occ = pd.read_parquet('curated/ocorrencias')
museu = pd.read_parquet('curated/museu')
faixaetaria = pd.read_parquet("curated/faixaetaria")
libras = pd.read_parquet("curated/libras")
regiao = pd.read_parquet('curated/regiao')
estados = pd.read_parquet('curated/estados')

estados['estado'] = estados.estado.str.title()

museu2 = museu[['id_museu', 'regiao', 'latitude',
                'longitude', 'nome', 'endereco', 'cidade', 'estado_completo']].copy()

inter = pd.merge(
    museu2,
    occ.iloc[:, [1, 2, 4, 5, 6, 7, -2, -1]],
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
inter['data_inicio'] = inter.data_inicio.astype(np.datetime64)
inter['data_fim'] = inter.data_fim.astype(np.datetime64)
