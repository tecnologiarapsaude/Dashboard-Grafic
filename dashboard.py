import pandas as pd
import requests
import streamlit as st
from datetime import timedelta


# def get_enterprise():

#     id_empresas = st.experimental_get_query_params().get('id_empresas', [None])[0]
    
#     if id_empresas:
#         # Validar e utilizar o token
#         # headers = {"Authorization": f"Bearer {id_empresas}"}
#         response = requests.get(f'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento?ID_empresa={[int(id_empresas)]}')

#         if response.status_code == 200:
#             user_data = response.json()
#             st.write("Dados do Usuário:", user_data)
#             date = user_data['lista_empresa']
#             st.write(date)
#             # id_empresas = date['empresas_id']
#             # st.write(id_empresas)
#         else:
#             st.error("Token inválido ou expiração.")
#     else:
#         st.error("Token não fornecido.")

#     return user_data['lista_empresa']


def fetch_data():

    ID_empresas = st.experimental_get_query_params().get('id_empresas', [None])[0]


    # Verifica se o parâmetro 'id_empresas' foi fornecido
    if ID_empresas is None:
        st.error("Parâmetro 'id_empresas' não fornecido na URL.")
        return None

    # Transforma o parâmetro em uma lista de inteiros
    try:
        # Supondo que os IDs sejam separados por vírgulas, ex: "1,2,3"
        id_empresas_list = [int(id_str) for id_str in ID_empresas.split(',')]
    except ValueError:
        st.error("O parâmetro 'id_empresas' deve ser uma lista de inteiros separados por vírgula.")
        return None

    # Construa a URL para a chamada à API
    # Converte a lista de inteiros em uma string separada por vírgulas
    id_empresas_str = ','.join(map(str, id_empresas_list))


    # URL do seu endpoint no Xano
    XANO_API_GET = f'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento'

    payload = {
        'ID_empresa':id_empresas_list
    }


    st.write(f'URL chamada: {payload}')

    try:
        # realizar a chamada get api
        response = requests.get(XANO_API_GET)
        st.write(response)

        # verificar se a respota foi bem sucedida
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')
            return response.json()  # Retorna os dados em formato JSON
        else:
            st.error(f"Erro: {response.status_code}")
            st.write(f"Detalhes do erro: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao fazer requisição: {str(e)}")
        return None


st.title("Integração com Xano")



st.write("""
# My first app
Hello world!
""")
    
# item = data[0]['aquivo_NF']['url']
# st.write(item)
# df = pd.read_csv(item)
# st.line_chart(df)

st.write(fetch_data())

st.write('''
    # Fim
    #FIM
''')