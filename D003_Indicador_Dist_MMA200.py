import MetaTrader5 as mt5
import pandas as pd
import glob
import os
from datetime import datetime
import talib as ta
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Inicializa o MT5
mt5.initialize()

# Escolher índice
ind = None
while ind not in [1, 2]:
    ind = int(input("Escolha os seguintes índices: 1 - IBOV, 2 - IBRA: "))
    ind1 = "IBOV" if ind == 1 else "IBRA"


# Localizar arquivo CSV
list_of_files = glob.glob(f"C:/Users/armen/OneDrive/Estratégias/Listas/{ind1}/*")
latest_file = max(list_of_files, key=os.path.getctime)
lista = pd.read_csv(
    latest_file,
    sep=";",
    encoding="ISO-8859-1",
    skiprows=0,
    skipfooter=2,
    engine="python",
    thousands=".",
    decimal=",",
    header=1,
    index_col=False,
)

df = pd.DataFrame(lista)
acoes = df["Código"].tolist()


periodo = 10000

afastamento = pd.DataFrame()
for acao in acoes:
    data = mt5.copy_rates_from(acao, mt5.TIMEFRAME_D1, datetime.today(), periodo)

    data = pd.DataFrame(data)
    data["time"] = pd.to_datetime(data["time"], unit="s")
    data.set_index("time", inplace=True)

    data["SMA_200"] = ta.SMA(data["close"], timeperiod=200)

    data["Afastamento"] = data["close"] - data["SMA_200"]

    afastamento[acao] = data["Afastamento"]

media_afastamento = afastamento.mean(axis=1)

# Criar o indicador de momento
indicador_momento = media_afastamento


indice = mt5.copy_rates_from(ind1, mt5.TIMEFRAME_D1, datetime.today(), periodo)
indice = pd.DataFrame(indice)
indice["time"] = pd.to_datetime(indice["time"], unit="s")
indice.set_index("time", inplace=True)




# Criar a figura com subplots
fig = make_subplots(rows=2, cols=1)

# Adicionar a linha do indicador de momento
fig.add_trace(
    go.Scatter(
        x=indicador_momento.index,
        y=indicador_momento,
        mode='lines',
        name='Indicador de Momento',
        line=dict(color='blue')
    ),
    row=1, col=1
)

# Adicionar linhas de referência para as zonas de sobrecompra e sobrevenda
fig.add_hline(y=2, line=dict(color="red", dash="dash"), row=1, col=1)
fig.add_hline(y=-2, line=dict(color="green", dash="dash"), row=1, col=1)
fig.add_hline(y=0, line=dict(color="black"), row=1, col=1)

fig.add_trace(
    go.Scatter(
        x=indice.index,
        y=indice["close"],
        mode='lines',
        name=f'{ind1}',
        line=dict(color='black')
    ),
    row=2, col=1
)




# Configurar layout do gráfico
fig.update_layout(
    title='Indicador de Momento do Mercado',
    xaxis_title='Data',
    yaxis_title='Afastamento Médio da SMA 200',
    legend_title='Indicadores',
    template='plotly_white'
)

# Exibir o gráfico
fig.show()