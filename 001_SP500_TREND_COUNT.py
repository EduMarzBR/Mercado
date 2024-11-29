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

n_acoes = len(acoes)
n_acao = 0
while n_acao < n_acoes:
    for acao in acoes:




        # download dataframe

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

        arr_alta.append(df[f"arr_alta {acao}"].astype(int))
        arr_baixa.append(df[f"arr_baixa {acao}"].astype(int))

        df_arr_alta = pd.concat(arr_alta, axis=1)
        df_arr_baixa = pd.concat(arr_baixa, axis=1)

        df3_alta[f"arr_alta"] = df_arr_alta.sum(axis=1)

        alta = df3_alta[f"arr_alta"].iloc[-1]

        df3_baixa[f"arr_baixa"] = df_arr_baixa.sum(axis=1)

        baixa = df3_baixa[f"arr_baixa"].iloc[-1]

        total_acoes = len(acoes)

        indefinida = total_acoes - alta - baixa

        print(acao,n_acao, n_acoes)
        n_acao += 1











acn = yf.download("^GSPC", start="2018-12-31", end=data_atual, interval="1d")
ind = pd.DataFrame(acn)

ind["mme9"] = mme9(ind)
ind["mme21"] = mme21(ind)

ind[f"alta"] = (ind["mme9"] > ind["mme21"]) & (ind["Adj Close"] > ind["mme21"])
ind[f"baixa"] = (ind["mme9"] < ind["mme21"]) & (ind["Adj Close"] < ind["mme21"])

ind[f"alta"] = ind[f"alta"].astype(int)
ind[f"baixa"] = ind[f"baixa"].astype(int)



if ind[f"alta"].iloc[-1] == 1:
    print(f"**Tendência do $SP500 no curto prazo: Alta**")
elif ind[f"baixa"].iloc[-1] == 1:
    print(f"**Tendência do $SP500 no curto prazo: Baixa**")
else:
    print(f"**Tendência do $SP500 no curto prazo: Indefinida**")


print("Total de ações:", total_acoes)
print("Alta:", round((alta/total_acoes)*100,2), "%")
print("Baixa:", round((baixa/total_acoes)*100,2), "%")
print("Indefinida:", round((indefinida/total_acoes)*100,2), "%")


# Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")