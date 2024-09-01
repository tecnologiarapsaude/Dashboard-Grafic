import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import datetime
import plotly.express as px

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
         
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')
            data = response.json()
            st.write(f'Esse é o json: {data}')
            
            dataframes = []

            for arquivo in data:
                created_at = arquivo['created_at'] / 1000
                created_at_date = datetime.fromtimestamp(created_at)
                st.write(f'Data de criação do arquivo: {created_at_date}')

                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    st.write('Arquivo CSV baixado com sucesso')
                    file_content = file_response.text
                    file_buffer = StringIO(file_content)
                    df = pd.read_csv(file_buffer)

                    df['created_at'] = created_at_date

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if len(dataframes) != 0:    
                # Tabela com o primeiro arquivo
                st.subheader("Dados do Primeiro Arquivo")
                st.dataframe(dataframes[0].head())

                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)
                combined_df = combined_df.dropna()

                # Gráfico com todos os dados misturados
                st.subheader("Gráfico com Todos os Dados")
                fig = px.scatter(combined_df, x='created_at', y='MENSALIDADE', color='EMPRESA', 
                                 title='Mensalidades por Data e Empresa')
                st.plotly_chart(fig)

                # Tabela com todos os valores concatenados
                st.subheader("Todos os Dados Concatenados")
                st.dataframe(combined_df)

                # Mantendo os filtros originais
                st.sidebar.header('Filtros')

                # Filtro de intervalo de datas
                min_date = combined_df['created_at'].min().date()
                max_date = combined_df['created_at'].max().date()
                selected_date_range = st.sidebar.slider(
                    'Selecione o intervalo de datas',
                    min_value=min_date,
                    max_value=max_date,
                    value=(min_date, max_date),
                    format="YYYY-MM-DD"
                )

                # Filtrar o DataFrame com base no intervalo de datas
                start_date, end_date = selected_date_range
                mask = (combined_df['created_at'].dt.date >= start_date) & (combined_df['created_at'].dt.date <= end_date)
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
                    filtered_df = filtered_df[filtered_df['EMPRESA'].isin(empresa_selecionada)]

                # Exibir o gráfico com os dados filtrados
                st.subheader("Gráfico Filtrado")
                st.line_chart(filtered_df.set_index('created_at')['MENSALIDADE'])

                # Gráfico de barras por empresa
                fig_empresa = px.bar(filtered_df, x='EMPRESA', y='MENSALIDADE', title='Mensalidade por Empresa')
                st.plotly_chart(fig_empresa)
                
            else:
                st.error("Nenhum arquivo CSV foi encontrado.")

        else:
            st.error(f"Erro: {response.status_code}")
            st.write(f"Detalhes do erro: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao fazer requisição: {str(e)}")
        return None

st.title("Visualização de Dados de Faturamento")

fetch_data()