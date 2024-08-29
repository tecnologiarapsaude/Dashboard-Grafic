import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import datetime

def fetch_data():
    # Trazendo id da empresa via o embed do WeWeb
    ID_empresas = st.experimental_get_query_params().get('id_empresas', [None])[0]

    if ID_empresas is None:
        st.error("Parâmetro 'id_empresas' não fornecido na URL.")
        return None

    try:
        # Transformando a lista de empresas de strings para inteiros
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
         
        # Pegando o JSON com as informações
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')
            data = response.json()
            st.write(f'Esse é o json: {data}')
            
            # Armazenar os DataFrames
            dataframes = []

            # Fazendo o loop para pegar todas as empresas no JSON e gerar o gráfico 
            for arquivo in data:
                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")
                st.write(f'Esse é os dados do arquivo detalhamento: {arquivo_detalhamento}')

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    st.write('Arquivo CSV baixado com sucesso')
                    file_content = file_response.text
                    file_buffer = StringIO(file_content)
                    df = pd.read_csv(file_buffer)

                    # Adicionando coluna 'created_at' para filtragem
                    df['created_at'] = datetime.fromtimestamp(arquivo['created_at'] / 1000)
                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if len(dataframes) != 0:    
                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)
                
                st.write(combined_df.head())

                # Gerar menu lateral com filtros
                st.sidebar.header('Filtros')

                # Filtrar por empresas
                empresa_selecionada = st.sidebar.multiselect(
                    'Selecione a empresa',
                    options=combined_df['EMPRESA'].unique(),
                    default=combined_df['EMPRESA'].unique(),
                    placeholder='Selecione a Empresa'
                )

                # Filtro por data de criação
                min_date = combined_df['created_at'].min().date()
                max_date = combined_df['created_at'].max().date()

                # Garantir que o retorno seja uma lista de duas datas
                date_range = st.sidebar.date_input(
                    'Selecione o intervalo de datas',
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )

                if isinstance(date_range, list) and len(date_range) == 2:
                    start_date, end_date = tuple(date_range)
                else:
                    st.error("Por favor, selecione um intervalo de datas válido.")
                    return None

                # Aplicar filtro de data
                mask = (combined_df['created_at'] >= pd.to_datetime(start_date)) & (combined_df['created_at'] <= pd.to_datetime(end_date))
                combined_df = combined_df[mask]

                # Aplicar filtro de empresa
                if empresa_selecionada:
                    # Filtrar dados com base na seleção da empresa
                    combined_df = combined_df[combined_df['EMPRESA'].isin(empresa_selecionada)]
                    # Criar os gráficos com os arquivos
                    st.line_chart(combined_df)
                else:
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
