import pandas as pd
import requests
import streamlit as st
from io import StringIO, BytesIO
from datetime import datetime
import plotly.express as px


def fetch_data():
    # Trazendo id da empresa via o embed do weweb
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

    XANO_API_GET = 'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento_teste_Post'
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

            # Armazenar os dataframes
            dataframes = []

            # Fazendo o for para pegar todas as empresas que estão no json e gerar o gráfico
            for arquivo in data:
                # Convertendo a data de vencimento em datetime
                data_vencimento_str = arquivo['data_vencimento']
                data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d')
                st.write(f'Data de criação do arquivo: {data_vencimento}')

                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    content_type = file_response.headers['Content-Type']
                    st.write(f'Tipo de conteúdo: {content_type}')

                    # Identificando o formato do arquivo
                    if 'csv' in content_type:
                        df = process_csv(file_response.text)
                    elif 'excel' in content_type:
                        df = process_excel(file_response.content)
                    elif 'text/plain' in content_type:
                        df = process_txt(file_response.text)
                    else:
                        st.error("Formato de arquivo não suportado.")
                        continue

                    # Adicionando informações padronizadas ao DataFrame
                    df = padronizar_dados(df, arquivo, data_vencimento)

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo: {file_response.status_code}")

            if dataframes:
                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)
                combined_df = combined_df.dropna()
                st.write(combined_df.head(100))

                # Aplicar os filtros e gerar gráficos
                aplicar_filtros_e_gerar_graficos(combined_df)

    except Exception as e:
        st.error(f"Erro ao chamar a API: {str(e)}")


def process_csv(content):
    """Processar arquivo CSV."""
    file_buffer = StringIO(content)
    df = pd.read_csv(file_buffer)
    return df


def process_excel(content):
    """Processar arquivo Excel."""
    file_buffer = BytesIO(content)
    df = pd.read_excel(file_buffer)
    return df


def process_txt(content):
    """Processar arquivo TXT delimitado."""
    # Aqui vamos assumir que o arquivo é delimitado por tabulação ou outro caractere.
    file_buffer = StringIO(content)
    try:
        df = pd.read_csv(file_buffer, delimiter='#')  # Alterar o delimitador conforme necessário
    except Exception as e:
        st.error(f"Erro ao processar o arquivo TXT: {str(e)}")
        return None
    return df


def padronizar_dados(df, arquivo, data_vencimento):
    """Padronizar colunas e adicionar informações ao DataFrame."""
    # Adicionando a data de vencimento ao DataFrame
    df['data_vencimento'] = data_vencimento

    # Adicionando Nome da Empresa
    empresa_id = arquivo['empresas_id']
    empresas = arquivo['_empresas']
    empresa_encontrada = next((empresa for empresa in empresas if empresa['id'] == empresa_id), None)
    df['Nome_Empresa'] = empresa_encontrada['nome_fantasia'] if empresa_encontrada else 'Empresa não encontrada'

    # Comparando operadoras_id com o id em _operadoras e obtendo Nome_Fantasia
    operadoras_id = arquivo['operadoras_id']
    operadoras = arquivo['_operadoras']
    df['Nome_Fantasia'] = operadoras['Nome_Fantasia'] if operadoras_id == operadoras['id'] else 'Operadora não encontrada'

    # Comparando status_faturas_id com o status_faturas
    status_faturas_id = arquivo['status_faturas_id']
    status_fatura = arquivo['_status_faturas']
    df['Status_Fatura'] = status_fatura['Status_Fatura'] if status_faturas_id == status_fatura['id'] else 'Status não encontrado'

    # _tipo_atendimento & 'tipo_atendimento_id'
    tipo_atendimento_id = arquivo['tipo_atendimento_id']
    tipo_atendimento = arquivo['_tipo_atendimento']
    df['Tipo_Atendimento'] = tipo_atendimento['Tipo_Atendimento'] if tipo_atendimento_id == tipo_atendimento['id'] else 'Tipo atendimento não existe'

    return df


def aplicar_filtros_e_gerar_graficos(combined_df):
    """Aplicar os filtros e gerar gráficos."""
    st.sidebar.header('Filtros')

    # Filtro de intervalo de datas ou mês atual
    filtro_opcao = st.sidebar.radio('Selecione o tipo de filtro', ('Mês atual', 'Intervalo de datas'))
    if filtro_opcao == 'Mês atual':
        current_month = datetime.now().month
        current_year = datetime.now().year
        mask = (combined_df['data_vencimento'].dt.month == current_month) & (combined_df['data_vencimento'].dt.year == current_year)
        filtered_df = combined_df.loc[mask]
    elif filtro_opcao == 'Intervalo de datas':
        min_date = combined_df['data_vencimento'].min().date()
        max_date = combined_df['data_vencimento'].max().date()
        selected_date_range = st.sidebar.slider('Selecione o intervalo de datas', min_value=min_date, max_value=max_date, value=(min_date, max_date), format="DD-MM-YYYY")
        start_date, end_date = selected_date_range
        mask = (combined_df['data_vencimento'].dt.date >= start_date) & (combined_df['data_vencimento'].dt.date <= end_date)
        filtered_df = combined_df.loc[mask]

    # Outros filtros: sexo, tipo de atendimento, operadora, empresa
    # Mapear o sexo para valores mais legíveis
    sexo_map = {'M': 'Masculino', 'F': 'Feminino'}
    sexo_selecionado = st.sidebar.multiselect('Selecione o Sexo', options=list(sexo_map.values()), default=list(sexo_map.values()))
    sexo_selecionado_originais = [key for key, value in sexo_map.items() if value in sexo_selecionado]
    filtered_df = filtered_df[filtered_df['SEXO'].isin(sexo_selecionado_originais)]

    # Filtro de tipo de atendimento
    tipo_atendimento_selecionado = st.sidebar.multiselect('Selecione o Tipo de Atendimento', options=filtered_df['Tipo_Atendimento'].unique(), default=filtered_df['Tipo_Atendimento'].unique())
    filtered_df = filtered_df[filtered_df['Tipo_Atendimento'].isin(tipo_atendimento_selecionado)]

    # Filtro por operadora e empresa
    operadora_selecionada = st.sidebar.multiselect('Selecione a Operadora', options=filtered_df['Nome_Fantasia'].unique(), default=filtered_df['Nome_Fantasia'].unique())
    filtered_df = filtered_df[filtered_df['Nome_Fantasia'].isin(operadora_selecionada)]

    empresa_selecionada = st.sidebar.multiselect('Selecione a empresa', options=filtered_df['Nome_Empresa'].unique(), default=filtered_df['Nome_Empresa'].unique())
    filtered_df = filtered_df[filtered_df['Nome_Empresa'].isin(empresa_selecionada)]

    # Exibir métricas
    col1, col2, col3 = st.columns(3)

    # Contagem de titulares e dependentes
    contagem_td = filtered_df['T/D'].value_counts()
    total_titulares = contagem_td.get('T', 0)
    total_dependentes = contagem_td.get('D', 0)
    total_vidas = filtered_df.shape[0]

    col1.metric(label="Total de Titulares", value=total_titulares)
    col2.metric(label="Total de Dependentes", value=total_dependentes)
    col3.metric(label="Total de Vidas", value=total_vidas)

    # Gerar gráfico
    fig = px.histogram(filtered_df, x='Nome_Empresa', color='T/D', barmode='group', title='Distribuição de Vidas por Empresa')
    st.plotly_chart(fig)


fetch_data()
