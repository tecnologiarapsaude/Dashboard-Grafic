import pandas as pd
import requests
import streamlit as st

def fetch_data():

    # trazendo id da empresa do weweb, pelo embed
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
    # id_empresas_str = ','.join(map(str, id_empresas_list))


    # URL do seu endpoint no Xano
    XANO_API_GET = f'https://xqyx-rytf-8kv4.n7d.xano.io/api:IVkUsJEe/arquivos_faturamento_teste_Post'

    payload = {
        'ID_empresa':id_empresas_list
    }


    st.write(f'URL chamada: {payload}')

    try:
        # realizar a chamada get api
        response = requests.post(XANO_API_GET, json=payload)
        st.write(response)

        # verificar se a respota foi bem sucedida
        if response.status_code == 200:
            st.write('Resposta recebida com sucesso')

            data = response.json()
            arquivo_url = data['arquivo_detalhamento_vidas']['url']

            return arquivo_url # Retorna os dados em formato JSON
        else:
            st.error(f"Erro: {response.status_code}")
            st.write(f"Detalhes do erro: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao fazer requisição: {str(e)}")
        return None
    
    # return response.json()
    
    
# data = response.json()

# arquivo_url = data['arquivo_detalhamento_vidas']['url']
# st.write(f'URL do arquivo: {arquivo_url}')

# df = pd.read_csv(arquivo_url)
# st.line_chart(df)


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

