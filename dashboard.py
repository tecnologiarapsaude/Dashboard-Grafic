import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import datetime
import plotly.express as px

def fetch_data():
    # Trazendo ID da empresa via o embed do WeWeb
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
            st.write(f'Esse é o JSON: {data}')
            
            # Armazenar os DataFrames
            dataframes = []

            # Fazendo o for para pegar todas as empresas que estão no JSON, e gerar o gráfico 
            for arquivo in data:
                data_vencimento = arquivo['data_vencimento']
                data_vencimento_date = pd.to_datetime(data_vencimento)
                st.write(f'Data de vencimento do arquivo: {data_vencimento_date}')

                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")
                st.write(f'Dados do arquivo detalhamento: {arquivo_detalhamento}')

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    st.write('Arquivo CSV baixado com sucesso')
                    file_content = file_response.text
                    file_buffer = StringIO(file_content)
                    df = pd.read_csv(file_buffer)

                    # Adicionando a data de vencimento ao DataFrame
                    df['data_vencimento'] = data_vencimento_date

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if dataframes:     
                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)

                # Remover ou substituir valores nulos na coluna 'data_vencimento'
                combined_df['data_vencimento'].fillna(pd.Timestamp.min, inplace=True)
                combined_df = combined_df.dropna()
                st.write(combined_df.head(100))

                # Gerar menu lateral com filtros
                st.sidebar.header('Filtros')

                # Filtro de intervalo de datas
                min_date = combined_df['data_vencimento'].min().date()
                max_date = combined_df['data_vencimento'].max().date()
                selected_date_range = st.sidebar.slider(
                    'Selecione o intervalo de datas',
                    min_value=min_date,
                    max_value=max_date,
                    value=(min_date, max_date),
                    format="YYYY-MM-DD"
                )

                # Filtrar o DataFrame com base no intervalo de datas
                start_date, end_date = selected_date_range
                mask = (combined_df['data_vencimento'].dt.date >= start_date) & (combined_df['data_vencimento'].dt.date <= end_date)
                filtered_df = combined_df.loc[mask]

                # Filtrar por empresas
                empresa_selecionada = st.sidebar.multiselect(
                    'Selecione a empresa',
                    options=filtered_df['EMPRESA'].unique(),
                    default=filtered_df['EMPRESA'].unique(),
                    placeholder='Selecione a Empresa'
                )

                if empresa_selecionada:
                    # Filtrar dados com base na seleção da empresa
                    dados_filtrados = filtered_df[filtered_df['EMPRESA'].isin(empresa_selecionada)]
                    filtered_df = dados_filtrados

                # Filtrar as colunas numéricas para evitar o erro de tipos mistos
                numeric_cols = filtered_df.select_dtypes(include=['float64', 'int64']).columns

                if not numeric_cols.empty:
                    fig_empresa = px.bar(filtered_df, x='EMPRESA', y=numeric_cols[0], title='Mensalidade por Empresa')
                    st.plotly_chart(fig_empresa)
                else:
                    st.error("Nenhuma coluna numérica disponível para renderizar o gráfico.")
                
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
