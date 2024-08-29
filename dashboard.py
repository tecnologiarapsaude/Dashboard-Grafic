import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import timedelta

def fetch_data():
    ID_empresas = st.experimental_get_query_params().get('id_empresas', [None])[0]

    if ID_empresas is None:
        st.error("Parâmetro 'id_empresas' não fornecido na URL.")
        return None

    try:
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
         
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')
            data = response.json()
            st.write(f'Esse é o json: {data}')
            
            dataframes = []

            for arquivo in data:
                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")
                st.write(f' Esse é os dados do aquivo detalhamento: {arquivo_detalhamento}')

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    st.write('Arquivo CSV baixado com sucesso')
                    file_content = file_response.text
                    file_buffer = StringIO(file_content)
                    df = pd.read_csv(file_buffer)

                    # Adicionar uma coluna de data
                    df['created_at'] = pd.to_datetime(arquivo['created_at'], unit='ms')
                    df.set_index('created_at', inplace=True)

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if len(dataframes) != 0:    
                combined_df = pd.concat(dataframes, ignore_index=False)
                
                st.write(combined_df.head())

                st.sidebar.header('Filtros')

                # Filtro por data usando slider
                data_inicial = combined_df.index.min().to_pydatetime()
                data_final = combined_df.index.max().to_pydatetime()

                intervalo_datas = st.sidebar.slider('Selecione as datas', 
                                                    min_value=data_inicial,
                                                    max_value=data_final, 
                                                    value=(data_inicial, data_final),
                                                    step=timedelta(days=1))

                dados_filtrados = combined_df.loc[intervalo_datas[0]:intervalo_datas[1]]

                # Filtro por empresa
                empresa_selecionada = st.sidebar.multiselect(
                    'Selecione a empresa',
                    options=dados_filtrados['EMPRESA'].unique(),
                    default=dados_filtrados['EMPRESA'].unique(),
                    placeholder='Selecione a Empresa'
                )

                if empresa_selecionada:
                    dados_filtrados = dados_filtrados[dados_filtrados['EMPRESA'].isin(empresa_selecionada)]
                    st.line_chart(dados_filtrados)
                else:
                    st.line_chart(dados_filtrados)                
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
