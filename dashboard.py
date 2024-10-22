import pandas as pd
import requests
import streamlit as st
from io import StringIO
from io import BytesIO
from datetime import datetime
import plotly.express as px
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import numpy as np
import os


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

    XANO_API_POST = f'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento_teste_Post'
    payload = {'ID_empresa': id_empresas_list}
    st.write(f'URL chamada: {payload}')

    try:
        response = requests.post(XANO_API_POST, json=payload)
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

                operadoras_id = arquivo['operadoras_id']
                operadoras = arquivo['_operadoras']
                st.write(operadoras['Nome_Fantasia'])

                file_response = requests.get(arquivo_url)
                if file_response.status_code == 200:

                    # Fazendo a verificação para pega o nome de cada operadora
                    if operadoras['Nome_Fantasia'] == 'Hapvida':
                        st.write('Arquivo Hapvida baixado com sucesso')
                        file_content = file_response.text
                        file_buffer = StringIO(file_content)
                        df = pd.read_csv(file_buffer, encoding='latin1', sep=';', skiprows=7)

                        st.write(df)

                        df.columns = ['Cd Contrato', 'Unidade','Empresa','Cd Beneficiário' ,'Matrícula', 'CPF', 'Beneficiário', 'Nome da Mãe', 'Data Nascimento', 'Data Exclusão', 'Idade', 'Dependência','Plano' ,'AC', 'Mensalidade', 'Adicional','Taxa Adesão' ,'Desconto','Valor Fatura',]

                        # Remover caracteres especiais e deixar apenas os números
                        # df['Código'] = df['Código'].str.replace(r'[^0-9]', '', regex=True)
                        
                        # Adicionando a data de vencimento ao DataFrame
                        df['data_vencimento'] = data_vencimento
                        dataframes.append(df)
                        
                    if operadoras['Nome_Fantasia'] == 'CNU':
                        st.write('Arquivo CNU baixado com sucesso')
                        file_content = file_response.content
                        file_buffer = BytesIO(file_content)
                        df = pd.read_excel(file_buffer, engine='openpyxl')

                        st.write(df)

                        df.columns = ['Data Competencia','Empresa', 'CNPJ' ,'Cd Beneficiário' ,'Matrícula','CPF Titular', 'Titular' , 'CPF' ,'Beneficiário', 'Data Nascimento', 'Idade', 'Sexo', 'Dependência', 'Vigencia', 'Data Exclusão', 'Cod_Plano','Plano' , 'Mensalidade', 'Valor Inscrição', 'Valor Fatura',]
                        
                        # Adicionando a data de vencimento ao DataFrame
                        df['data_vencimento'] = data_vencimento
                        dataframes.append(df)
                    
                    if operadoras['Nome_Fantasia'] == 'Amil':
                        st.write('Arquivo Amil baixado com sucesso')
                        file_content = file_response.text
                        file_buffer = StringIO(file_content)

                        # Lê o arquivo como texto completo
                        df = pd.read_csv(file_buffer, encoding='latin1', skiprows=5, sep='#')

                        st.write(df)

                        # Define os nomes das colunas conforme a estrutura dos dados
                        df.columns = ['Cd Beneficiário', 'Beneficiário', 'Matrícula', 'CPF', 'Plano', 'Dependência', 'Idade', 'Tipo', 'Data Limite', 'Data Inclusão', 'Data Exclusão', 'Lotacão', 'Rubrica', 'Co-Participacao', 'Outros', 'Valor Fatura', 'Total Família']

                        # Adicionando a data de vencimento ao DataFrame
                        df['data_vencimento'] = data_vencimento
                        dataframes.append(df)

                    if operadoras['Nome_Fantasia'] == 'GNDI':
                        st.write('Arquivo GNDI baixado com sucesso')
                        file_content = file_response.text
                        file_buffer = StringIO(file_content)

                        # Lê o arquivo como texto completo
                        df = pd.read_csv(file_buffer, encoding='latin1', sep=';', index_col=False)

                        st.write(df)

                        # Define os nomes das colunas conforme a estrutura dos dados
                        df.columns = ['Mês Ano Competencia','Cd Contrato','Empresa', 'Tipo Faturamento','Cd Beneficiário', 'Matrícula','Titular' ,'Beneficiário','Sexo','Dependência','Data Nascimento','Data Vigencia contrato','Data Vigencia associado','Cod_Plano','Plano','CPF', 'Total Vidas gp Familiar', 'Valor Fatura','Valor Retroativo','Cd Local Trabalho','CNPJ', 'Rubrica', 'Cd Unico Cliente', 'Lotacão']

                        # Adicionando a data de vencimento ao DataFrame
                        df['data_vencimento'] = data_vencimento

                        # Colocando tipo da coluna
                        df['Cd Beneficiário'] = df['Cd Beneficiário'].astype(str)

                        st.write(df)

                        dataframes.append(df)

                    empresa_id = arquivo['empresas_id']
                    empresas = arquivo['_empresas']

                    empresa_encontrada = next((empresa for empresa in empresas if empresa['id'] == empresa_id), None)

                    if empresa_encontrada:
                        df['Nome_Empresa'] = empresa_encontrada['nome_fantasia']
                    else:
                        df['Nome_Empresa'] = 'Empresa não encontrada'

                    # Comparando operadoras_id com o id em _operadoras e obtendo Nome_Fantasia

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
                # combined_df = combined_df.dropna()
                st.write(combined_df)

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
                sexo_map = {'M': 'Masculino', 'F': 'Feminino', 'None': 'Não Informado'}

                # Adicionando o filtro de sexo
                sexo_selecionado = st.sidebar.multiselect(
                    'Selecione o Sexo',
                    options=list(sexo_map.values()),
                    default=list(sexo_map.values()),
                    placeholder='Selecione o Sexo'
                )

                # Filtrar valores não nulos ou não informados
                filtered_df = filtered_df.fillna('None')

                # Reverter o mapeamento do sexo pelos os valores Originais
                sexo_selecionado_originais = [key for key, value in sexo_map.items() if value in sexo_selecionado]

                if sexo_selecionado_originais:
                    # Filtrar dados com base na seleção de sexo
                    dados_filtrados = filtered_df[filtered_df['Sexo'].isin(sexo_selecionado_originais)]
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

                # Filtro Titular e Dependente
                td_selecionado = st.sidebar.multiselect(
                    'Selecione o Tipo de Vínculo',
                    options=filtered_df['Dependência'].unique(),
                    default=filtered_df['Dependência'].unique(),
                    placeholder='Selecione o Tipo de Vínculo'
                )

                if td_selecionado:
                    # Filtrar dados com base na seleção do tipo de vínculo
                    dados_filtrados = filtered_df[filtered_df['Dependência'].isin(td_selecionado)]
                    filtered_df = dados_filtrados    

                # filtro por Operadoras
                operadora_selecionada = st.sidebar.multiselect(
                    'Selecione a Operadora',
                    options=filtered_df['Nome_Fantasia'].unique(),
                    default=filtered_df['Nome_Fantasia'].unique(),
                    placeholder='Selecione a Operadora'
                )

                if operadora_selecionada:
                    # Filtrar dados com base na seleção da operadora
                    dados_filtrados = filtered_df[filtered_df['Nome_Fantasia'].isin(operadora_selecionada)]
                    filtered_df = dados_filtrados

                # Filtrar por empresas
                empresa_selecionada = st.sidebar.multiselect(
                    'Selecione a empresa',
                    options=filtered_df['Empresa'].unique(),
                    default=filtered_df['Empresa'].unique(),
                    placeholder='Selecione a Empresa'
                )

                if empresa_selecionada:
                    # Filtrar dados com base na seleção da empresa
                    dados_filtrados = filtered_df[filtered_df['Empresa'].isin(empresa_selecionada)]
                    filtered_df = dados_filtrados

                # Exibir o gráfico com os dados filtrados ou o DataFrame original se o filtro estiver vazio
                # st.line_chart(filtered_df if not filtered_df.empty else combined_df)
                st.write(filtered_df.head(50))
                # st.write()

                # Graficos de distribuição de vidas
                st.title('Distribuição de Vidas')

                # criando colunas paras tres cards
                col1, col2, col3 = st.columns(3)

                # Criando um container para separar os conteudos das colunas
                # Contagem de TD 
                contagem_td = filtered_df['Dependência'].value_counts()
                # Obtendo o total de titulares e dependentes
                total_titulares = contagem_td.get('TITULAR', 0)
                total_dependentes = contagem_td.get('D', 0)
                with st.container():
                    with col1:
                        # pegando o total de vidas do dataframe
                        total_vidas = filtered_df['Beneficiário'].count()
                        st.metric(label="Total de Vidas", value=f'{total_vidas:,}')

                    with col2:
                        # pegando o total de titular do dataframe
                        st.metric(label='Total de Titulares' , value=f'{total_titulares:,}')

                    with col3:  
                        # pegando o total de dependentes do dataframe 
                        # OBS:Não tem a tabela dependentes foi colocada outra tabela
                        st.metric(label='Total de Dependentes', value=f'{total_dependentes:,}')

                # Container dos graficos de vidas em cada sexo e distribuiçao por vinculo
                with st.container():
                #     # criado colunas para separa os graficos
                    col_vidas_operadora,col_distribuicao_vinculo = st.columns(2) 

                    # Grafico de Vidas em cada operadora com streamlit
                    with col_vidas_operadora:
                        # fazendo a contagem de quantas vidas tem cada operadora
                        total_vidas = filtered_df['Sexo'].value_counts().sort_index().reset_index().replace('None', 'Não Informado')
                        total_vidas.columns = ['Sexo','total_vidas'] #renomendo as tabelas do dataframe
                        vidas_operadoras = px.pie(
                            total_vidas, 
                            names='Sexo', 
                            values='total_vidas', 
                            title='DISTRIBUIÇÃO POR SEXO',
                            labels={'Sexo':'Sexo','total_vidas':'Total de Vidas'},
                            color='total_vidas',
                            hole=.6,
                            color_discrete_sequence=['skyblue', 'blue', 'orange']
                            )
                        st.plotly_chart(vidas_operadoras)

                    # Grafico de distribuição por vinculos com streamlit
                    with col_distribuicao_vinculo:

                        filtered_df['Categoria'] = np.where(filtered_df['Dependência'].isin(['T', 'TITULAR']), 'Titular', 'Dependente')
                        total_vinculos = filtered_df['Categoria'].value_counts().sort_index().reset_index()
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

                # grafico de custo por operadora com streamlit
                with st.container():
                    #filtered_df[' COBRADO '] = pd.to_numeric(filtered_df[' COBRADO '], errors='coerce')
                    # df_total_valor= filtered_df[' COBRADO '].sum()
                    total_operadora = filtered_df['Nome_Fantasia'].value_counts().sort_index().reset_index()
                    total_operadora.columns = ['Operadora', 'Total Operadoras']
                    st.write(total_operadora)
                    # st.write(filtered_df[' COBRADO '].dtype)
                    custo_operadora = px.bar(
                        total_operadora, 
                        x='Operadora', 
                        y='Total Operadoras', 
                        title='Distribuição por Operadoras',
                        labels={'Nome_Fantasia':'Operadora','Total Operadora':'Total Operadora'},
                        color='Operadora',  # Adiciona uma cor baseada na contagem
                        color_continuous_scale='Blues'
                        )
                    st.plotly_chart(custo_operadora)

                
                # # preparar o grafico com streamlit faixa etaria e sexo
                # with st.container():
                #     total_idades = filtered_df['Idade'].value_counts().sort_index().reset_index()
                #     total_idades.columns = ['Idade', 'Total_idades']
                #     distribuicao_faixa_sexo = px.bar(
                #         total_idades, 
                #         x='Idade', 
                #         y='Total_idades', 
                #         title='Distribuição por Faixa Etária e Sexo',
                #         labels={'Idade': 'Idade', 'Total_idades': 'Total Pessoas'},
                #         color='Idade',  # Adiciona uma cor baseada na contagem
                #         color_continuous_scale='Blues')  # Paleta de cores, ajuste conforme desejado)
                #     st.plotly_chart(distribuicao_faixa_sexo)

                # # Grafico do estilo funil para faixa etaria e sexo
                # with st.container():
                    
                #     filtered_df['Idade'] = pd.to_numeric(filtered_df['Idade'], errors='coerce')

                #     # Optional: Drop rows where 'Idade' is NaN
                #     filtered_df = filtered_df.dropna(subset=['Idade'])


                #     condicao_faixa_etaria = [
                #         (filtered_df['Idade'] > 59),
                #         (filtered_df['Idade'] > 49) & (filtered_df['Idade'] <= 59),
                #         (filtered_df['Idade'] > 39) & (filtered_df['Idade'] <= 49),
                #         (filtered_df['Idade'] > 29) & (filtered_df['Idade'] <= 39),
                #         (filtered_df['Idade'] > 17) & (filtered_df['Idade'] <= 29),
                #         (filtered_df['Idade'] <= 17)

                #     ]
                #     opcoes = ['Maior que 60 Anos', '50 - 59 Anos','40 - 49 Anos','30 - 39 Anos','18 - 29 Anos', '0 - 17 Anos']

                #     filtered_df['faixa_etaria'] = np.select(condicao_faixa_etaria, opcoes, default='Não Definido')

                #     df_grouped = filtered_df.groupby(['faixa_etaria', 'Sexo']).size().reset_index()
                #     df_grouped.columns = ['Faixa_etaria','Sexo','Total']

                #     df_masculino = df_grouped[df_grouped['Sexo'] == 'M'].reset_index(drop=True)
                #     df_feminino = df_grouped[df_grouped['Sexo'] == 'F'].reset_index(drop=True)

                #     df = pd.concat([df_masculino, df_feminino], axis=0)
                #     fig = px.funnel(
                #         df, 
                #         x='Total', 
                #         y='Faixa_etaria', 
                #         color='Sexo',
                #         title='Distribuição por Faixa Etária e Sexo',
                #         labels={'Idade':'Idades','Total':'Total de Idades'}
                #         )

                #     # Ajustar o gráfico para parecer um funil empilhado
                #     fig.update_layout(
                #         barmode='stack',  # Empilha as barras
                #         xaxis_title='Total de Pessoas',
                #         yaxis_title='Faixa Etária',
                #         yaxis=dict(
                #             categoryorder='total descending'  # Ordena as faixas etárias do maior para o menor
                #         ),
                #         xaxis=dict(
                #             title='Total de Pessoas'
                #         )
                #     )


                #     st.write(df)

                #     # Exibir o gráfico no Streamlit  
                #     st.plotly_chart(fig) 

                    filtered_df['Idade'] = pd.to_numeric(filtered_df['Idade'], errors='coerce')
                    # Optional: Drop rows where 'Idade' is NaN
                    filtered_df = filtered_df.dropna(subset=['Idade'])


                    total_idade = filtered_df['Idade'].value_counts().sort_index().reset_index()
                    total_idade.columns = ['Idade', 'Total Idades']
                    st.write(total_idade)
                    # st.write(filtered_df[' COBRADO '].dtype)
                    custo_idade = px.bar(
                        total_idade, 
                        x='Idade', 
                        y='Total Idades', 
                        title='Distribuição por Idades',
                        labels={'Idade':'Idade','Total idades':'Total Idades'},
                        color='Idade',  # Adiciona uma cor baseada na contagem
                        color_continuous_scale='Blues'
                        )
                    st.plotly_chart(custo_idade)               
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
