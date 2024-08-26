import pandas as pd
import requests
import streamlit as st
from datetime import timedelta

token = st.experimental_get_query_params().get('token', [None])[0]

if token:
     # Validar e utilizar o token
     headers = {"Authorization": f"Bearer {token}"}
     response = requests.get("https://xqyx-rytf-8kv4.n7d.xano.io/api:Z8VtHP2l/auth/me", headers=headers)
     if response.status_code == 200:
            user_data = response.json()
            st.write("Dados do Usuário:", user_data)
            date = user_data['lista_empresa']
            st.write(date)
     else:
         st.error("Token inválido ou expiração.")
else:
     st.error("Token não fornecido.")



st.write("Token:", token)
def fetch_data(ID_empresa):

    # URL do seu endpoint no Xano
    XANO_API_GET = f'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento?ID_empresa={[int(ID_empresa)]}'

    st.write(f'URL chamada: {XANO_API_GET}')


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


st.write('''
    # Fim
    #FIM
''')