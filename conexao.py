import pandas as pd
import numpy as np
import os


tabelas = [
        'lab4_ricardo_celso.eventos', 
        'lab4_ricardo_celso.ocorrencias', 
        'lab4_ricardo_celso.museu', 
        'lab4_ricardo_celso.libras', 
        'lab4_ricardo_celso.faixaetaria', 
        'lab4_ricardo_celso.frequencia', 
        'lab4_ricardo_celso.estados', 
        'lab4_ricardo_celso.regiao'
]


def registrar_localmente_bd():
    from pyodbc import connect
    import toml


    conditions = [
        os.path.exists('curated/estados'),
        os.path.exists('curated/ocorrencias'),
        os.path.exists('curated/museu'),
    ]

    if not all(conditions):
        
        if not os.path.exists('curated'): os.mkdir('curated')

        arquivos = [x.path for x in os.scandir('curated\\') if x.is_file()]
        for arq in arquivos: os.unlink(f'curated\\{arq}')
        

        CONFIG = toml.load('base_dados_info.toml')['config']
        AUTHENTICATION = 'ActiveDirectoryInteractive'

        # STRING P/ CONEXÃO EM BD:
        txt_conexao = \
        f"DRIVER={CONFIG['driver']};\
        SERVER={CONFIG['server']};\
        PORT={CONFIG['port']};\
        DATABASE={CONFIG['database']};\
        UID={CONFIG['username']};\
        AUTHENTICATION={AUTHENTICATION};"

        Authentication = 'ActiveDirectoryInteractive'

        with connect(txt_conexao) as cursor:
            for tabela in tabelas:
                result = cursor.execute(f'select * from {tabela}')                
                cols = [column[0] for column in result.description]
                
                result = result.fetchall()
                result = [list(x) for x in result]

                tab = tabela.split('.')[-1]

                df = pd.DataFrame(result)
                df.columns = cols

                if tab == 'regiao':
                    df.iloc[:, -1] = df.iloc[:, -1].str.title()
                if tab == 'museu':
                    df.rename(columns={'estado':'sigla_estado'}, inplace=True)
                df.to_parquet(f'curated\\{tab}', index=None)
        
            
registrar_localmente_bd()


if not os.path.exists('curated\\alternativas'): os.mkdir('curated\\alternativas')

if not os.listdir('curated\\alternativas'):
    eventos = pd.read_parquet("curated\\eventos")
    occ = pd.read_parquet('curated\\ocorrencias')
    museu = pd.read_parquet('curated\\museu')
    faixaetaria = pd.read_parquet("curated\\faixaetaria")
    libras = pd.read_parquet("curated\\libras")
    regiao = pd.read_parquet('curated\\regiao')
    estados = pd.read_parquet('curated\\estados')

    estados['estado'] = estados.estado.str.title()
    museu.rename(columns={'geoestado': 'estado_completo'}, inplace=True)
    museu.columns = [col.replace(' ', '_') for col in museu.columns]
    occ.columns = [col.replace(' ', '_') for col in occ.columns]

    museu['regiao'] = museu.regiao.replace(
        dict(regiao.values)).copy()
    
    museu['sigla_estado'] = museu.sigla_estado.replace(
        dict(estados[['id_estados', 'sigla']].values)).copy()
    
    museu['estado_completo'] = museu.estado_completo.replace(
        dict(estados[['id_estados', 'estado']].values)).copy()

    museu.to_parquet('curated\\museu')

    museu2 = museu[['id_museu', 'regiao', 'latitude',
                    'longitude', 'nome', 'endereco', 'cidade', 'sigla_estado', 'estado_completo']].copy()

    occ['spaceId'] = occ.spaceId.astype(int)


    inter = pd.merge(
        museu2,
        occ.iloc[:, [1, 2, 4, 5, 6, 7, -2, -1]],
        left_on='id_museu',
        right_on='spaceId',
        how='right'
    )

    eventos.columns = [col.replace(' ', '_') for col in eventos.columns]
    eventos.rename({'nome': 'nome_evento'}, axis=1, inplace=True)
    eventos.to_parquet('curated\\eventos')


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


    museu2.to_parquet('curated\\alternativas\\museu2', index=None)


    inter['regiao'] = inter.regiao.replace(dict(regiao.values))
    inter['regiao'] = inter.regiao.astype("category")
    
    inter['estado_completo'] = inter['estado_completo'].replace(
        dict(estados[['id_estados', 'estado']].values)).copy()


    inter.to_parquet('curated\\alternativas\\inter', index=None)

    occ_temp = occ[['id_occ', 'eventId', 'spaceId', 'data_inicio',
                    'hora_inicio', 'hora_fim', 'data_fim', 'timezone', 'preco']]

    event_temp = eventos[['id_eventos', 'nome_evento', 'faixa_etaria', 'descricao_longa',
                          'descricao_curta', 'telefone', 'traducao_libras', 'info_para_registro',
                          'site']]


    museu_temp = museu2[['id_museu', 'regiao', 'nome', 'endereco',
                         'cidade', 'estado_completo']].copy()

    museu_temp.rename({'nome': 'nome_museu'}, axis=1, inplace=True)

    relat = pd.merge(
        occ_temp,
        museu_temp,
        left_on='spaceId',
        right_on='id_museu',
        how='left'
    )

    relat = pd.merge(
        event_temp,
        relat,
        left_on='id_eventos',
        right_on='eventId',
        how='right'
    )

    relat = relat[[
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

    relat['faixa_etaria'] = relat.faixa_etaria.replace(
        dict(faixaetaria.values)).copy()

    relat['traducao_libras'] = relat.traducao_libras.replace(
        dict(libras.values)).copy()

    relat['estado_completo'] = relat['estado_completo'].replace(
        dict(estados[['id_estados', 'estado']].values)).copy()

    relat['regiao'] = relat.regiao.replace(dict(regiao.values))

    relat.to_parquet('curated\\alternativas\\relat', index=None)


eventos = pd.read_parquet("curated\\eventos")
occ = pd.read_parquet('curated\\ocorrencias')
museu = pd.read_parquet('curated\\museu')
faixaetaria = pd.read_parquet("curated\\faixaetaria")
libras = pd.read_parquet("curated\\libras")
regiao = pd.read_parquet('curated\\regiao')
estados = pd.read_parquet('curated\\estados')
inter = pd.read_parquet('curated\\alternativas\\inter')
museu2 = pd.read_parquet('curated\\alternativas\\museu2')
relat = pd.read_parquet('curated\\alternativas\\relat')