import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import timedelta

def fetch_data():
    # trazendo id da empresa via o embed do weweb
    ID_empresas = st.experimental_get_query_params().get('id_empresas', [None])[0]

    if ID_empresas is None:
        st.error("Parâmetro 'id_empresas' não fornecido na URL.")
        return None

    try:
        # transformando a lista de empresas de strings para inteiros
        id_empresas_list = [int(id_str) for id_str in ID_empresas.split(',')]
    except ValueError:
        st.error("O parâmetro 'id_empresas' deve ser uma lista de inteiros separados por vírgula.")
        return None

    XANO_API_GET = f'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento_teste_Post'
    payload = {'ID_empresa': id_empresas_list}
    st.write(f'URL chamada: {payload}')

    try:
        response = requests.post(XANO_API_GET, json=payload)
        st.write(response)
         
        # pegando o json com as informaçoes
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')
            data = response.json()
            
            # armazenar os dataframes
            dataframes = []

            # fazendo o for para pega todas as empresa que estao no json, e gerar o grafico 
            for arquivo in data:
                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    st.write('Arquivo CSV baixado com sucesso')
                    file_content = file_response.text
                    file_buffer = StringIO(file_content)
                    df = pd.read_csv(file_buffer)

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if len(dataframes) == 2:    
                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)
                
                st.write(combined_df.head())

                # gerar menu lateral com filtros
                st.sidebar.header('Filtros')

                # Filtros por data
                st.write(combined_df.index.dtype)
                data_inicial = combined_df.index.min().to_pydatetime()
                data_final = combined_df.index.max().to_pydatetime()

                intervalo_datas = st.sidebar.slider('Selecione as datas',
                                                    min_value=data_inicial,
                                                    max_value=data_final,
                                                    value=(data_inicial, data_final),
                                                    step=timedelta(days=1))
                combined_df = combined_df.loc[intervalo_datas[0]:intervalo_datas[1]]

                # Criar o graficos com os arquivos
                st.line_chart(combined_df)
            
            else:
                st.error("Menos de dois arquivos CSV foram encontrados.")

        else:
            st.error(f"Erro: {response.status_code}")
            st.write(f"Detalhes do erro: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao fazer requisição: {str(e)}")
        return None

st.title("Integração com Xano")


st.write(fetch_data())
