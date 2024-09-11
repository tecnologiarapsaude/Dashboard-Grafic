import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import datetime
import plotly.express as px
import streamlit.components.v1 as components
import matplotlib.pyplot as plt


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
            st.write(f'Esse é o json: {data}')

            # armazenar os dataframes
            dataframes = []

            # fazendo o for para pegar todas as empresas que estão no json, e gerar o gráfico
            for arquivo in data:
                # Convertendo a data de vencimento em datetime
                data_vencimento_str = arquivo['data_vencimento'] 
                data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d')
                st.write(f'Data de criação do arquivo: {data_vencimento}')

                arquivo_detalhamento = arquivo['arquivo_detalhamento_vidas']
                arquivo_url = arquivo_detalhamento['url']
                st.write(f"URL do arquivo: {arquivo_url}")
                st.write(f' Esse é os dados do arquivo detalhamento: {arquivo_detalhamento}')

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:
                    st.write('Arquivo CSV baixado com sucesso')
                    file_content = file_response.text
                    file_buffer = StringIO(file_content)
                    df = pd.read_csv(file_buffer)

                    # Adicionando a data de vencimento ao DataFrame
                    df['data_vencimento'] = data_vencimento

                    # Comparando operadoras_id com o id em _operadoras e obtendo Nome_Fantasia
                    operadoras_id = arquivo['operadoras_id']
                    operadoras = arquivo['_operadoras']

                    if operadoras_id == operadoras['id']:
                        df['Nome_Fantasia'] = operadoras['Nome_Fantasia']
                    else:
                        df['Nome_Fantasia'] = 'Operadora não encontrada'

                    # Comparando status_faturas_id com o status_faturas
                    status_faturas_id = arquivo['status_faturas_id']
                    status_fatura = arquivo['_status_faturas']

                    if status_faturas_id == status_fatura['id']:
                        df['Status_Fatura'] = status_fatura['Status_Fatura']
                    else:
                        df['Status_Fatura'] = 'Status não encontrado'

                    # _tipo_atendimento & 'tipo_atendimento_id
                    tipo_atendimento_id = arquivo['tipo_atendimento_id']
                    tipo_atendimento = arquivo['_tipo_atendimento']

                    if tipo_atendimento_id == tipo_atendimento['id']:
                        df['Tipo_Atendimento'] = tipo_atendimento['Tipo_Atendimento']
                    else:
                        df['Tipo_Atendimento'] = 'Tipo atendimento não existe'

                    dataframes.append(df)
                else:
                    st.error(f"Erro ao baixar o arquivo CSV: {file_response.status_code}")

            if dataframes:
                # Concatenar os DataFrames
                combined_df = pd.concat(dataframes, ignore_index=True)
                combined_df = combined_df.dropna()
                st.write(combined_df.head(100))

                # gerar menu lateral com filtros
                st.sidebar.header('Filtros')

                if len(dataframes) > 1:
                    # Filtro de intervalo de datas
                    min_date = combined_df['data_vencimento'].min().date()
                    max_date = combined_df['data_vencimento'].max().date()
                    selected_date_range = st.sidebar.slider(
                        'Selecione o intervalo de datas',
                        min_value=min_date,
                        max_value=max_date,
                        value=(min_date, max_date),
                        format="DD-MM-YYYY"
                    )

                    # Filtrar o DataFrame com base no intervalo de datas
                    start_date, end_date = selected_date_range
                    mask = (combined_df['data_vencimento'].dt.date >= start_date) & (combined_df['data_vencimento'].dt.date <= end_date)
                    filtered_df = combined_df.loc[mask]
                else:
                    filtered_df = combined_df
                
                #Filtro por Nome_Fantasia da Operadora
                operadora_selecionada = st.sidebar.multiselect(
                    'Selecione a Operadora',
                    options=filtered_df['Nome_Fantasia'].unique(),
                    default=filtered_df['Nome_Fantasia'].unique(),
                    placeholder='Selecione a Operadora'
                )

                if operadora_selecionada:
                    # Filtrar dados com base na seleção da empresa
                    dados_filtrados = filtered_df[filtered_df['Nome_Fantasia'].isin(operadora_selecionada)]
                    filtered_df = dados_filtrados
                #Filtrar por Status_Fatura
                status_fatura_selecionada = st.sidebar.multiselect(
                    'Selecione o Status Fatura',
                    options=filtered_df['Status_Fatura'].unique(),
                    default=filtered_df['Status_Fatura'].unique(),
                    placeholder='Selecione o Status Fatura'
                )

                if status_fatura_selecionada:
                    dados_filtrados = filtered_df[filtered_df['Status_Fatura'].isin(status_fatura_selecionada)]
                    filtered_df = dados_filtrados

                # Filtro por Tipo de Atendimento
                tipo_atendimento_selecionado = st.sidebar.multiselect(
                    'Selecione o Tipo de Atendimento',
                    options = filtered_df['Tipo_Atendimento'].unique(),
                    default=filtered_df['Tipo_Atendimento'].unique(),
                    placeholder="Selecione o Tipo de atendimento"
                )

                if tipo_atendimento_selecionado:
                    dados_filtrados = filtered_df[filtered_df['Tipo_Atendimento'].isin(tipo_atendimento_selecionado)]
                    filtered_df = dados_filtrados

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

                # Exibir o gráfico com os dados filtrados ou o DataFrame original se o filtro estiver vazio
                st.line_chart(filtered_df if not filtered_df.empty else combined_df)
                st.write(filtered_df.head(50))
                # st.write()

                st.sidebar.header('Filtros')

                fig_empresa = px.bar(filtered_df, x='Nome_Fantasia', y='MENSALIDADE', title='Mensalidade por Empresa')
                st.plotly_chart(fig_empresa)

                # Graficos de distribuição de vidas
                st.title('Distribuição de Vidas')

                # criando colunas paras tres cards
                col1, col2, col3 = st.columns(3)

                # Criando um container para separar os conteudos das colunas
                with st.container():
                    with col1:
                        # pegando o total de vidas do dataframe
                        total_vidas = filtered_df['BENEFICIARIO'].count()
                        st.metric(label="Total de Vidas", value=f'{total_vidas:,}')

                    with col2:
                        # pegando o total de titular do dataframe
                        total_titular = filtered_df['TITULAR'].count()
                        st.metric(label='Total de Titulares' , value=f'{total_titular:,}')

                    with col3:  
                        # pegando o total de dependentes do dataframe 
                        # OBS:Não tem a tabela dependentes foi colocada outra tabela
                        total_dependentes = filtered_df['MATRICULA'].count()
                        st.metric(label='Total de Dependentes', value=f'{total_dependentes:,}')

                # grafico de custo por operadora com streamlit
                custo_operadora = px.bar(filtered_df, x='Nome_Fantasia', y=' COBRADO ', title='Custo por Operadoras')
                st.plotly_chart(custo_operadora)

                # grafico de distribuição por faixa etaria e sexo
                
                # Combine 'ID' e 'Sexo' em uma nova coluna
                # filtered_df['ID_Sexo'] = filtered_df['ID'].astype(str) + ' - ' + filtered_df['SEXO']


                # preparar o grafico com matplotlib faixa etaria e sexo
                with st.container():
                    total_idades = filtered_df['ID'].value_counts().sort_index()
                    plt.figure(figsize=(10, 6))
                    total_idades.plot(kind='bar',  color='skyblue', edgecolor='white')
                    plt.xlabel('Idade', color='white')
                    plt.ylabel('Total Pessoas', color='white')
                    # Alterar a cor dos números dos eixos (ticks)
                    plt.tick_params(axis='x', colors='white')  # Cor dos números no eixo X
                    plt.tick_params(axis='y', colors='white')  # Cor dos números no eixo Y
                    plt.title('Distribuição por Faixa Etária', color='white')
                    plt.grid(True, linestyle='--', alpha=0.3, color='white')
                    plt.tight_layout()
                    plt.gca().set_facecolor('#0e1117') #ALTERANDO A COR DE FUNDO
                    plt.gcf().patch.set_facecolor('#0e1117')
                    st.pyplot()


                ## grafico de distribuição por faixa etaria e sexo com streamlit
                # total_idades1 = filtered_df['ID'].value_counts().sort_index()
                total_idades1 = filtered_df['ID'].value_counts().sort_index()
                total_idades1.columns = ['ID', 'Total_idades']
                st.write(total_idades1)
                distribuicao_faixa_sexo = px.bar(
                    total_idades1, 
                    x='ID', 
                    y='Total_idades', 
                    title='Distribuição por Faixa Etária e Sexo',
                    labels={'ID': 'Idade', 'Total_idades': 'Total Pessoas'},
                    color='red',  # Adiciona uma cor baseada na contagem
                    color_continuous_scale='Blues')  # Paleta de cores, ajuste conforme desejado)
                


                st.plotly_chart(distribuicao_faixa_sexo)
                
                # Grafico de Vidas em cada operadora com matplotlib

                # fazendo a contagem de quantas vidas tem cada operadora
                total_vidas = filtered_df['Nome_Fantasia'].value_counts().sort_index()
                plt.figure(figsize=(10, 6)) 
                total_vidas.plot(kind='bar', color='skyblue', edgecolor='white')
                plt.xlabel('Operadoras', color='white')
                plt.ylabel('Total de vidas', color='white')
                # Alterar a cor dos números dos eixos (ticks)
                plt.tick_params(axis='x', colors='white')  # Cor dos números no eixo X
                plt.tick_params(axis='y', colors='white')  # Cor dos números no eixo Y
                plt.title('Vidas por Operadoras', color='white')
                plt.grid(True, linestyle='--', alpha=0.3, color='white')
                plt.tight_layout()
                plt.gca().set_facecolor('#0e1117') #ALTERANDO A COR DE FUNDO 
                plt.gcf().patch.set_facecolor('#0e1117')
                st.pyplot()

                st.write(total_vidas)

                # Grafico de Vidas em cada operadora com streamlit 
                vidas_operadoras = px.bar(filtered_df, x='Nome_Fantasia', y='ID', title='Vidas por Operadora')
                st.plotly_chart(vidas_operadoras)
            
            
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
