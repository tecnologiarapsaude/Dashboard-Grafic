import pandas as pd
import requests
import streamlit as st
from io import StringIO
from datetime import datetime
import plotly.express as px
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import numpy as np


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

                    empresa_id = arquivo['empresas_id']
                    empresas = arquivo['_empresas']

                    empresa_encontrada = next((empresa for empresa in empresas if empresa['id'] == empresa_id), None)

                    if empresa_encontrada:
                        df['Nome_Empresa'] = empresa_encontrada['nome_fantasia']
                    else:
                        df['Nome_Empresa'] = 'Empresa não encontrada'

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

                # Opção de filtro: intervalo de datas ou por mês atual
                filtro_opcao = st.sidebar.radio(
                    'Selecione o tipo de filtro',
                    ('Mês atual','Intervalo de datas')
                )

                # Filtro de intervalo de datas
                if filtro_opcao == 'Mês atual':
                    # Filtro para o mês atual
                    current_month = datetime.now().month
                    current_year = datetime.now().year
                    mask = (combined_df['data_vencimento'].dt.month == current_month) & (combined_df['data_vencimento'].dt.year == current_year)
                    filtered_df = combined_df.loc[mask]

                # Filtro de intervalo de datas
                elif filtro_opcao == 'Intervalo de datas':
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

                # Mapear o sexo para valores mais legíveis
                sexo_map = {'M': 'Masculino', 'F': 'Feminino'}

                # Adicionando o filtro de sexo
                sexo_selecionado = st.sidebar.multiselect(
                    'Selecione o Sexo',
                    options=list(sexo_map.values()),
                    default=list(sexo_map.values()),
                    placeholder='Selecione o Sexo'
                )

                # Reverter o mapeamento do sexo pelos os valores Originais
                sexo_selecionado_originais = [key for key, value in sexo_map.items() if value in sexo_selecionado]

                if sexo_selecionado_originais:
                    # Filtrar dados com base na seleção de sexo
                    dados_filtrados = filtered_df[filtered_df['SEXO'].isin(sexo_selecionado_originais)]
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
                    options=filtered_df['Nome_Empresa'].unique(),
                    default=filtered_df['Nome_Empresa'].unique(),
                    placeholder='Selecione a Empresa'
                )

                if empresa_selecionada:
                    # Filtrar dados com base na seleção da empresa
                    dados_filtrados = filtered_df[filtered_df['Nome_Empresa'].isin(empresa_selecionada)]
                    filtered_df = dados_filtrados

                # Exibir o gráfico com os dados filtrados ou o DataFrame original se o filtro estiver vazio
                st.line_chart(filtered_df if not filtered_df.empty else combined_df)
                st.write(filtered_df.head(50))
                # st.write()

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
                with st.container():
                    # Verificar se a coluna é numérica e converter se necessário
                    filtered_df[' COBRADO '] = pd.to_numeric(df[' COBRADO '], errors='coerce')
                    filtered_df['total_valor'] = filtered_df[' COBRADO '].sum(axis=0)
                    
                    # st.write(filter)
                    custo_operadora = px.bar(
                        filtered_df, 
                        x='Nome_Fantasia', 
                        y='total_valor', 
                        title='Custo por Operadoras',
                        labels={'Nome_Fantasia':'Operadora',' COBRADO ':'Valor Cobrado'},
                        color='Nome_Fantasia',  # Adiciona uma cor baseada na contagem
                        color_continuous_scale='Blues'
                        )
                    st.plotly_chart(custo_operadora)

                
                # preparar o grafico com streamlit faixa etaria e sexo
                with st.container():
                    total_idades = filtered_df['ID'].value_counts().sort_index().reset_index()
                    total_idades.columns = ['Idade', 'Total_idades']
                    distribuicao_faixa_sexo = px.bar(
                        total_idades, 
                        x='Idade', 
                        y='Total_idades', 
                        title='Distribuição por Faixa Etária e Sexo',
                        labels={'Idade': 'Idade', 'Total_idades': 'Total Pessoas'},
                        color='Idade',  # Adiciona uma cor baseada na contagem
                        color_continuous_scale='Blues')  # Paleta de cores, ajuste conforme desejado)
                    st.plotly_chart(distribuicao_faixa_sexo)

                # teste do grafico do estilo funil para faixa etaria e sexo
                with st.container():

                    condicao_faixa_etaria = [
                        (filtered_df['ID'] > 59),
                        (filtered_df['ID'] > 49) & (filtered_df['ID'] <= 59),
                        (filtered_df['ID'] > 39) & (filtered_df['ID'] <= 49),
                        (filtered_df['ID'] > 29) & (filtered_df['ID'] <= 39),
                        (filtered_df['ID'] > 17) & (filtered_df['ID'] <= 29),
                        (filtered_df['ID'] <= 17)
                    ]
                    opcoes = ['Maior que 60 Anos', '50 - 59 Anos','40 - 49 Anos','30 - 39 Anos','18 - 29 Anos', '0 - 17 Anos']

                    filtered_df['faixa_etaria'] = np.select(condicao_faixa_etaria, opcoes, default='Não Definido')

                    df_grouped = filtered_df.groupby(['faixa_etaria', 'SEXO']).size().reset_index()
                    df_grouped.columns = ['Faixa_etaria','Sexo','Total']

                    df_masculino = df_grouped[df_grouped['Sexo'] == 'M'].reset_index(drop=True)
                    df_feminino = df_grouped[df_grouped['Sexo'] == 'F'].reset_index(drop=True)

                    df = pd.concat([df_masculino, df_feminino], axis=0)
                    fig = px.funnel(
                        df, 
                        x='Total', 
                        y='Faixa_etaria', 
                        color='Sexo',
                        title='Distribuição por Faixa Etária e Sexo',
                        labels={'Idade':'Idades','Total':'Total de Idades'}
                        )

                    # Ajustar o gráfico para parecer um funil empilhado
                    fig.update_layout(
                        barmode='stack',  # Empilha as barras
                        xaxis_title='Total de Pessoas',
                        yaxis_title='Faixa Etária',
                        yaxis=dict(
                            categoryorder='total descending'  # Ordena as faixas etárias do maior para o menor
                        ),
                        xaxis=dict(
                            title='Total de Pessoas'
                        )
                    )


                    st.write(df)

                    # Exibir o gráfico no Streamlit  
                    st.plotly_chart(fig)


                # Container dos graficos de vidas em cada operadora e distribuiçao por vinculo
                with st.container():
                    # criado colunas para separa os graficos
                    col_vidas_operadora,col_distribuicao_vinculo = st.columns(2) 

                    # Grafico de Vidas em cada operadora com streamlit
                    with col_vidas_operadora:
                        # fazendo a contagem de quantas vidas tem cada operadora
                        total_vidas = filtered_df['Nome_Fantasia'].value_counts().sort_index().reset_index()
                        total_vidas.columns = ['nome_operadora','total_vidas'] #renomendo as tabelas do dataframe
                        vidas_operadoras = px.pie(
                            total_vidas, 
                            names='nome_operadora', 
                            values='total_vidas', 
                            title='Vidas por Operadora',
                            labels={'nome_operadora':'Nome da Operadora','total_vidas':'Total de Vidas'},
                            color='total_vidas',
                            hole=.6,
                            color_discrete_sequence=['skyblue', 'blue']
                            )
                        st.plotly_chart(vidas_operadoras)

                    # Grafico de distribuição por vinculos com streamlit
                    with col_distribuicao_vinculo:
                        total_vinculos = filtered_df['T/D'].value_counts().sort_index().reset_index()
                        total_vinculos.columns = ['nome_vinculo','total_vinculo']
                        grafico_vinculo = px.pie(
                            total_vinculos,
                            title='Vinculos',
                            names='nome_vinculo',
                            values='total_vinculo',
                            labels={'nome_vinculo':'Nome do Vinculo','total_vinculo':'Total de Vinculos'},
                            color='nome_vinculo',
                            hole=.6,)
                        st.plotly_chart(grafico_vinculo)
            
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
