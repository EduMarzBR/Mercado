import os
import pandas as pd
import glob
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime

list_of_files = glob.glob(r"C:\Users\armen\OneDrive\Estratégias\Listas\IBRA\*")  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)


# Caminho para a pasta que contém os arquivos CSV
caminho_pasta = r"C:\Users\armen\OneDrive\Estratégias\Base\Diária"

# Lista de ativos
lista = pd.read_csv(latest_file, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python',
                    thousands='.', decimal=',', header=1, index_col=False)

df1 = pd.DataFrame(lista)

lista = df1['Código']

ibra = pd.read_csv(r"C:\Users\armen\OneDrive\Estratégias\Base\Diária\IBRA_B_0_Diário.csv", sep=';',
                  encoding='ISO-8859-1', skiprows=0, skipfooter=0, engine='python', thousands='.', decimal=',',)

ibra['Data'] = pd.to_datetime(ibra['Data'], format="%d/%m/%Y")

ibra = ibra.sort_values(by="Data")

datas = ibra["Data"]


def calcular_diferenca_percentual(volume_atual, volume_medio):
    if volume_medio == 0:
        return 0
    return ((volume_atual - volume_medio) / volume_medio) * 100

v_acima_media = pd.DataFrame()
v_acima_media["Data"] = datas
v_acima_media["Data"]= pd.to_datetime(v_acima_media["Data"], format="%d/%m/%Y")
for ativo in lista:
    # Montar o caminho completo do arquivo CSV
    caminho_arquivo = os.path.join(caminho_pasta, f"{ativo}_B_0_Diário.csv")
    if os.path.exists(caminho_arquivo):
        # Carregar o arquivo CSV utilizando o pandas
        df = pd.read_csv(caminho_arquivo, sep=';',
                      encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python', thousands='.', decimal=',',
                      header=0, index_col=False)

        # Converter a coluna de data para o formato de data
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
        
        # Ordenar o DataFrame pela coluna de data em ordem crescente
        df = df.sort_values(by="Data")
        #Calcular a média móvel do volume para 21 períodos corridos
        df["Média Movel"] = df["Volume"].rolling(21).mean()
        # Calcular o percentual de superação do volume atual em relação ao volume médio de 21 períodos
        df["Volume 100% Acima da Media"] = ((df["Volume"] - df["Média Movel"]) / df["Média Movel"] * 100)>100
        #Cria um novo DataFrame com as colunas Data e Volume 100% Acima da Media
        v_a_m = pd.DataFrame()
        v_a_m["Data"] = df["Data"]
        v_a_m["Data"] = pd.to_datetime(v_a_m["Data"], format="%d/%m/%Y")
        v_a_m[f"{ativo}"] = df["Volume 100% Acima da Media"].astype('int64')
        # Faz um merge entre o DataFrame v_acima_media e o DataFrame v_a_m
        v_acima_media = pd.merge(v_acima_media, v_a_m, how="left", on="Data")

#Transformar True e False em 1 e 0




v_acima_media = v_acima_media.fillna(0)


exclui_datas = v_acima_media.drop('Data', axis=1)
v_acima_media["Contagem"] = exclui_datas.sum(axis=1)
v_acima_media.set_index("Data", inplace=True)

ibra["Data"] = pd.to_datetime(ibra["Data"], format="%d/%m/%Y")
ibra.set_index("Data", inplace=True)

#Mudar o nome das colunas
ibra.rename(columns={'Abertura': 'Open', 'Fechamento': 'Close', 'Máximo': 'High', 'Mínimo': 'Low',},inplace=True)

ibra_200 = ibra.iloc[-200:]
v_acima_media_200 = v_acima_media.iloc[-200:]

fig = make_subplots(rows=2, cols=1, shared_xaxes=True)



# Adicione o gráfico de linha do NH_NL_I e do NH_NL_I_Media_Movel na primeira linha

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Candlestick", "Gráfico de Barras"))

# Adicione o gráfico de candlestick ao primeiro subplot
fig.add_trace(go.Candlestick(x=ibra_200.index,
                             open=ibra_200['Open'],
                             high=ibra_200['High'],
                             low=ibra_200['Low'],
                             close=ibra_200['Close'],
                             name='Candlestick'), row=1, col=1)

# Adicione o gráfico de barras ao segundo subplot
fig.add_trace(go.Bar(x=v_acima_media_200.index, y=v_acima_media_200['Contagem'], name='Gráfico de Barras'), row=2, col=1)

# Atualize os layouts dos subplots
fig.update_layout(title_text="Estudo de variação do Volume", title_font=dict(size=20))
fig.update_xaxes(title_text="Data", row=2, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="IBRA", row=1, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Contagem", row=2, col=1, title_font=dict(size=16))
fig.update_legends(font=dict(size=15))
fig.update_annotations(dict(
    xref="paper", yref="paper",
    x=0, y=-0.1,
))


# Exiba os subplots
fig.show()



