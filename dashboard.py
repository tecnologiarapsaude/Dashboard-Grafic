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
         
        # Pegando o json com as informações
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')
            data = response.json()
            st.write(f'Esse é o json: {data}')
            
            # Gerar menu lateral com filtros
            st.sidebar.header('Filtros')

            # Extraindo as datas de criação (created_at) para filtrar
            created_at_dates = [datetime.fromtimestamp(arquivo['created_at'] / 1000).date() for arquivo in data]

            # Definindo o intervalo de datas para o slider
            min_date = min(created_at_dates)
            max_date = max(created_at_dates)
            selected_date_range = st.sidebar.slider(
                'Selecione o intervalo de datas',
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD"
            )

            # Filtrar os dados JSON com base no intervalo de datas selecionado
            start_date, end_date = selected_date_range
            filtered_data = [arquivo for arquivo in data if start_date <= datetime.fromtimestamp(arquivo['created_at'] / 1000).date() <= end_date]

            # Se nenhum filtro de data estiver ativo, use todos os dados
            if len(filtered_data) == 0:
                filtered_data = data

            # Armazenar os dataframes
            dataframes = []

            # Fazendo o loop para pegar todas as empresas que estão no JSON e gerar o gráfico 
            for arquivo in filtered_data:
                created_at_date = datetime.fromtimestamp(arquivo['created_at'] / 1000)
                st.write(f'Data de criação do arquivo: {created_at_date}')

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

                    # Adicionando a data de criação ao DataFrame
                    df['created_at'] = created_at_date

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if len(dataframes) != 0:    
                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)
                
                st.write(combined_df.head())

                # Filtrar por empresas
                empresa_selecionada = st.sidebar.multiselect(
                    'Selecione a empresa',
                    options=combined_df['EMPRESA'].unique(),
                    default=combined_df['EMPRESA'].unique(),
                    placeholder='Selecione a Empresa'
                )

                if empresa_selecionada:
                    # Filtrar dados com base na seleção da empresa
                    dados_filtrados = combined_df[combined_df['EMPRESA'].isin(empresa_selecionada)]
                    combined_df = dados_filtrados

                # Exibir o gráfico com os dados filtrados ou o DataFrame completo se o filtro estiver vazio
                if not combined_df.empty:
                    st.line_chart(combined_df)
                else:
                    st.error("Nenhum dado disponível para exibição no gráfico.")

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
