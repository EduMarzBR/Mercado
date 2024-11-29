import yfinance as yf
import requests
from bs4 import BeautifulSoup
import warnings
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import talib

warnings.filterwarnings("ignore")

def get_sector(ticker):
    return yf.Ticker(ticker).info["sector"]

def calculate_atr(data, period=14):
    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    # Calcular True Range (TR)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).dropna()

    # Verificar se há valores ausentes no True Range
    if true_range.isnull().any():
        raise ValueError(
            "Os dados contêm valores ausentes. Certifique-se de preencher ou remover esses valores."
        )

    # Verificar se o período é menor ou igual ao número de dados disponíveis
    if period > len(true_range):
        raise ValueError(
            "O período especificado é maior do que a quantidade de dados disponíveis."
        )

    # Calcular o ATR
    atr = true_range.rolling(window=period, min_periods=1).mean()

    return atr

def mme9(data):
    mme9 = data["Adj Close"].ewm(span=9, adjust=False).mean()
    return mme9

def mme21(data):
    mme21 = data["Adj Close"].ewm(span=21, adjust=False).mean()
    return mme21

def corpo(data):
    corpo = data["Close"] - data["Open"]
    return corpo







# URL da página da web que contém a tabela
url = "http://www.slickcharts.com/sp500"

# Enviar uma solicitação GET para a página
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}
response = requests.get(url, headers=headers)

# Verificar se a solicitação foi bem-sucedida
if response.status_code == 200:
    # Analisar o conteúdo HTML da página usando BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Encontre a tabela desejada com base em sua classe, ID ou outros atributos
    tabela = soup.find(
        "table", {"class": "table table-hover table-borderless table-sm"}
    )

    # Verificar se a tabela foi encontrada
    if tabela:
        # Inicialize listas vazias para cada coluna
        coluna1 = []
        coluna2 = []
        coluna3 = []
        coluna4 = []

        # Agora você pode extrair os dados da tabela conforme necessário
        for linha in tabela.find_all("tr"):
            colunas = linha.find_all("td")
            if len(colunas) >= 3:
                coluna1.append(colunas[0].text.strip())
                coluna2.append(colunas[1].text.strip())
                # Substitua os pontos por hifens na coluna3, se houver
                coluna3.append(colunas[2].text.strip().replace(".", "-"))
                coluna4.append(colunas[3].text.strip().replace("%", ""))

        # Crie um DataFrame com as colunas extraídas
        df = pd.DataFrame({"Symbol": coluna3, "Peso": coluna4})

        # Exiba o DataFrame

    else:
        print("Tabela não encontrada na página.")

else:
    print("Falha na solicitação à página da web.")

# Cria uma lista usando a coluna 'Symbol'
acoes = df["Symbol"].apply(lambda x: "GEV-WI" if x == "GEVw" else x)
weights = df["Peso"].apply(lambda x: float(x)/100)




yf.set_tz_cache_location("custom/cache/location")

#Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")




# Criar DataFrames vazios
df3_alta = pd.DataFrame()
df3_baixa = pd.DataFrame()
# Criar listas vazias
arr_alta = []
arr_baixa = []

for acao, peso in zip(acoes, weights):
    # download dataframe
    print(acao)
    if acao == "2318605D":
        acao = "BG"

    acn = yf.download(acao, start="2018-12-31", end=data_atual)
    df = pd.DataFrame(acn)

    # Remover os NaN resultantes do cálculo
    #df = df.dropna()



    df["mme9"] = mme9(df)
    df["mme21"] = mme21(df)


    df[f"arr_alta {acao}"] = ((df["mme9"] > df["mme21"])
        & (df["Adj Close"] > df["mme21"])
    )
    df[f"arr_baixa {acao}"] = ((df["mme9"] < df["mme21"])
        & (df["Adj Close"] < df["mme21"])
    )

    arr_alta.append(df[f"arr_alta {acao}"].astype(int)*peso)
    arr_baixa.append(df[f"arr_baixa {acao}"].astype(int)*peso)

    df_arr_alta = pd.concat(arr_alta, axis=1)
    df_arr_baixa = pd.concat(arr_baixa, axis=1)

    df3_alta[f"arr_alta"] = df_arr_alta.sum(axis=1)

    per_df3 = 9
    df3_alta[f"arr_alta_media"] = df3_alta["arr_alta"].ewm(span=per_df3, adjust=True).mean()
    df3_alta[f"arr_alta_mm"] = df3_alta["arr_alta_media"].ewm(span=per_df3, adjust=True).mean()
#    df3_alta[f"arr_alta_mm"] = df3_alta[f"arr_alta_mm1"].ewm(span=per_df3, adjust=True).mean()

    df3_baixa[f"arr_baixa"] = df_arr_baixa.sum(axis=1)
    df3_baixa[f"arr_baixa_media"] = df3_baixa["arr_baixa"].ewm(span=per_df3, adjust=True).mean()
    df3_baixa[f"arr_baixa_mm"] = df3_baixa["arr_baixa_media"].ewm(span=per_df3, adjust=True).mean()
#    df3_baixa[f"arr_baixa_mm"] = df3_baixa["arr_baixa_mm1"].ewm(span=per_df3, adjust=True).mean()




periodo = -500
# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
df4_alta_250 = df3_alta.iloc[periodo:]
df4_baixa_250 = df3_baixa.iloc[periodo:]
saldo = pd.DataFrame()
saldo['Arrancada'] = df4_alta_250['arr_alta'] - df4_baixa_250['arr_baixa']
per_saldo = 21
saldo['Arrancada media'] = saldo['Arrancada'].ewm(span=per_saldo, adjust=True).mean()

acn = yf.download("^GSPC", start="2018-12-31", end=data_atual, interval="1d")
ind = pd.DataFrame(acn)

ind_250 = ind[periodo:]






# Crie subplots com três linhas (uma para cada gráfico)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True)



# # Adicione o gráfico de linha da LAD IBRA
fig.add_trace(go.Bar(x=saldo.index, y=saldo['Arrancada'], name='IFT'), row=1, col=1)
fig.add_trace(go.Scatter(x=saldo.index, y=saldo['Arrancada media'], mode='lines', name=f'MME {per_saldo}', line=dict(color='red')), row=1, col=1)
fig.add_trace(go.Scatter(x=ind_250.index, y=ind_250['Adj Close'], mode='lines', name='S&P 500', line=dict(color='black')), row=2, col=1)


fig.add_annotation(
    text="Fonte: Yahoo Finance, SlickCharts e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper", yref="paper",
    x=0, y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray")
)




fig.update_layout(title_text=f"Índice de Força de Tendência | Ponderado pelo Peso de Cada Ação no Índice | S&P 500 - {dt}", title_font=dict(size=20))
fig.update_yaxes(title_text="IFT", row=1, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="S&P 500", row=2, col=1, title_font=dict(size=16))

fig.update_legends(font=dict(size=15))
fig.update_annotations(dict(
    xref="paper", yref="paper",
    x=0, y=-0.1,
))




# Exiba os subplots
fig.show()