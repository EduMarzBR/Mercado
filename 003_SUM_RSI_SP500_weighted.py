import pandas as pd
from pandas_datareader import data as pdr
import datetime
import yfinance as yf
import talib
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")

def n_ampl_index_cp(alta, baixa):
    # Calcula o n_ampl Index
    n_ampl_cp = alta - baixa

    return n_ampl_cp


def n_ampl_index_lp(alta, baixa):
    # Calcula o n_ampl Index
    n_ampl_lp = alta - baixa

    return n_ampl_lp








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

        # Agora você pode extrair os dados da tabela conforme necessário
        for linha in tabela.find_all("tr"):
            colunas = linha.find_all("td")
            if len(colunas) >= 3:
                coluna1.append(colunas[1].text.strip())
                coluna2.append(colunas[2].text.strip().replace(".", "-"))
                # Substitua os pontos por hifens na coluna3, se houver
                coluna3.append(colunas[3].text.strip().replace("%", ""))

        # Crie um DataFrame com as colunas extraídas
        df = pd.DataFrame({"Symbol": coluna2, "Weight": coluna3})

        # Exiba o DataFrame

    else:
        print("Tabela não encontrada na página.")

else:
    print("Falha na solicitação à página da web.")

# Cria uma lista usando a coluna 'Symbol'
acoes = df["Symbol"].apply(lambda x: "GEV-WI" if x == "GEVw" else x)
weights = df["Weight"].apply(lambda x: float(x) / 100)


yf.set_tz_cache_location("custom/cache/location")

data_atual = datetime.date.today()
dt = data_atual.strftime("%d/%m/%Y")

# Criar um DataFrame vazio para armazenar os resultados
resultados = pd.DataFrame()
dfs_temp = []
RSI_resultados = []

# Calcular os Altas e declínios de cada dia
dfs_alta_cp = []
dfs_baixa_cp = []
dfs_alta_cp_lp = []
dfs_baixa_lp = []
# Calcular os avanços e declínios de cada dia
dfs_advances = []
dfs_declines = []
dfs_vol_adv = []
dfs_vol_dec = []

# Loop através de cada ação
for acao, peso in zip(acoes, weights):
    # download dataframe
    print(acao)
    if acao == "2318605D":
        acao = "BG"

    acn = yf.download(acao, start="2021-01-01", end=data_atual)
    df = pd.DataFrame(acn)

    # Calcular as novas altas e baixas nos últimos 252 dias
    df["Nova_Alta"] = df["Adj Close"].rolling(252).max()
    df["Nova_Baixa"] = df["Adj Close"].rolling(252).min()

    # Remover os NaN resultantes do cálculo
    df = df.dropna()

    # Verificar se a ação fez nova máxima e nova mínima em relação aos últimos 252 dias
    df["Fez_Nova_Alta"] = df["Adj Close"] == df["Nova_Alta"]
    df["Fez_Nova_Baixa"] = df["Adj Close"] == df["Nova_Baixa"]

    # Adicionar os resultados ao DataFrame de resultados
    novo_frame = df[["Fez_Nova_Alta", "Fez_Nova_Baixa"]].astype(int)
    resultados = resultados.copy()
    resultados = pd.concat([resultados, novo_frame], axis=1)
    resultados.columns = resultados.columns.str.replace(
        "Fez_Nova_Alta", acao + "_Nova_Alta"
    )
    resultados.columns = resultados.columns.str.replace(
        "Fez_Nova_Baixa", acao + "_Nova_Baixa"
    )

    resultados[acao + "_Nova_Alta"] = resultados[acao + "_Nova_Alta"] * peso
    resultados[acao + "_Nova_Baixa"] = resultados[acao + "_Nova_Baixa"] * peso

    # Calcular a Linha de Avaço e Declínio do SP500
    df1 = pd.DataFrame(acn)

    condition_1 = df1["Adj Close"].diff()

    df1["signal"] = condition_1 > 0

    # Armazenar o DataFrame temporário na lista

    dfs_temp.append(df1["signal"].astype(int).apply(lambda x: peso if x == 1 else -peso))

    # Calcular somatória de sobrecomprados e sobrevendidos
    df2 = pd.DataFrame(acn)
    df2["RSI"] = talib.RSI(df2["Adj Close"], timeperiod=14)
    df2["RSI_gt_70"] = df2["RSI"] > 70
    df2["RSI_lw_30"] = df2["RSI"] < 30
    RSI_resultados.append(df2[["RSI_gt_70", "RSI_lw_30"]].astype(int)*peso)

    mme9 = df1["Adj Close"].ewm(span=9, adjust=True).mean()
    mme21 = df1["Adj Close"].ewm(span=21, adjust=True).mean()
    mme50 = df1["Adj Close"].ewm(span=50, adjust=True).mean()
    mme200 = df1["Adj Close"].ewm(span=200, adjust=True).mean()
    fech = df1["Adj Close"]

    df["Alta"] = (fech > mme9) & (mme9 > mme21)
    df["Baixa"] = (fech < mme9) & (mme9 < mme21)
    df["Alta_lp"] = (fech > mme50) & (mme50 > mme200)
    df["Baixa_lp"] = (fech < mme50) & (mme50 < mme200)

    # Armazenar o DataFrame temporário na lista
    dfs_alta_cp.append(df["Alta"].astype(int))
    dfs_baixa_cp.append(df["Baixa"].astype(int))
    dfs_alta_cp_lp.append(df["Alta_lp"].astype(int))
    dfs_baixa_lp.append(df["Baixa_lp"].astype(int))

    #McClellan Oscillator
    condition_1 = df1["Adj Close"].diff()

    df1["Avanço"] = condition_1 > 0
    df1["Declinio"] = condition_1 < 0

    # Armazenar o DataFrame temporário na lista
    dfs_advances.append(df1["Avanço"].astype(int))
    dfs_declines.append(df1["Declinio"].astype(int))

    # Adicionar volumes às listas para as linhas em que "Avanço" é verdadeiro
    if df1["Avanço"].any():
        dfs_vol_adv.append(df1.loc[df1["Avanço"], "Volume"])

    # Adicionar volumes/Dk listas para as linhas em que "Declinio" é verdadeiro
    if df1["Declinio"].any():
        dfs_vol_dec.append(df1.loc[df1["Declinio"], "Volume"])


# Calcular o número total de ações que fizeram nova alta e nova baixa em cada dia
resultados["Total_Nova_Alta"] = resultados.filter(like="_Nova_Alta").sum(axis=1)
resultados["Total_Nova_Baixa"] = resultados.filter(like="_Nova_Baixa").sum(axis=1)
resultados["NH_NL_I"] = (resultados["Total_Nova_Alta"] - resultados["Total_Nova_Baixa"])

resultados["NH_NL_I"].fillna(0, inplace=True)
resultados["NH_NL_I_Media_Movel_10"] = resultados["NH_NL_I"].rolling(window=10).mean()


# Calcular a média móvel dos últimos 20 dias de resultados['NH_NL_I']
resultados["NH_NL_I_Media_Movel"] = (
    resultados["NH_NL_I_Media_Movel_10"].rolling(window=10).mean()
)
resultados["NH_NL_I_Media_Movel"].fillna(0, inplace=True)


# Concatenar os DataFrames temporários para criar df3
df3 = pd.concat(dfs_temp, axis=1)

# Substituir 0 por -1 em todo o DataFrame
#df3.replace(0, -1, inplace=True)

# Calcular a coluna "Soma" usando a vetorização
df3["Soma"] = df3.sum(axis=1)

# Calcular a coluna "addc", LAD
df3["addc1"] = df3["Soma"].cumsum()
df3["addc"] = df3["addc1"].ewm(span=7, adjust=True).mean()

# Calcular a média móvel de addc, LAD
df3["addc_MMA"] = df3["addc"].rolling(window=21).mean()


# Concatenar os resultados de todos os ativos do RSI_resultados
merged_df = pd.concat(RSI_resultados)

merged_df = merged_df.groupby(merged_df.index).sum()


# Concatenar os DataFrames temporários para criar dfs_high
dfs_high = pd.concat(dfs_alta_cp, axis=1)
dfs_high_lp = pd.concat(dfs_alta_cp_lp, axis=1)

# Calcular a coluna "Soma" usando a vetorização
dfs_high["Soma"] = dfs_high.sum(axis=1)
dfs_high_lp["Soma"] = dfs_high_lp.sum(axis=1)

# Concatenar os DataFrames temporários para criar dfs_dowm
dfs_dowm = pd.concat(dfs_baixa_cp, axis=1)
dfs_dowm_lp = pd.concat(dfs_baixa_lp, axis=1)


# Calcular a coluna "Soma" usando a vetorização
dfs_dowm["Soma"] = dfs_dowm.sum(axis=1)
dfs_dowm_lp["Soma"] = dfs_dowm_lp.sum(axis=1)


data1 = pd.DataFrame()


data1["High"] = dfs_high["Soma"]
data1["Down"] = dfs_dowm["Soma"]
data1["High_lp"] = dfs_high_lp["Soma"]
data1["Down_lp"] = dfs_dowm_lp["Soma"]

df4 = pd.DataFrame(data1)

n_ampl_cp = n_ampl_index_cp(df4["High"], df4["Down"])

n_ampl_cp = pd.DataFrame(n_ampl_cp)

n_ampl_lp = n_ampl_index_lp(df4["High_lp"], df4["Down_lp"])

n_ampl_lp = pd.DataFrame(n_ampl_lp)

# Adiciona as colunas ao DataFrame original com nomes específicos
n_ampl = pd.concat([n_ampl_cp, n_ampl_lp], axis=1)
n_ampl.columns = ["Nova Amplitude CP", "Nova Amplitude LP"]
n_ampl = pd.DataFrame(n_ampl)
n_ampl_180 = n_ampl.iloc[-200:]


# Concatenar os DataFrames temporários para criar df_av
df_av = pd.concat(dfs_advances, axis=1)

# Calcular a coluna "Soma" usando a vetorização
df_av["Soma"] = df_av.sum(axis=1)


# Concatenar os DataFrames temporários para criar df_dec
df_dec = pd.concat(dfs_declines, axis=1)

# Calcular a coluna "Soma" usando a vetorização
df_dec["Soma"] = df_dec.sum(axis=1)


df_vol_adv = pd.concat(dfs_vol_adv, axis=1)

df_vol_adv["Soma"] = df_vol_adv.sum(axis=1)

df_vol_dec = pd.concat(dfs_vol_dec, axis=1)

df_vol_dec["Soma"] = df_vol_dec.sum(axis=1)


data = pd.DataFrame()


data["Advances"] = df_av["Soma"]
data["Declines"] = df_dec["Soma"]
data["Volume Advances"] = df_vol_adv["Soma"]
data["Volume Declines"] = df_vol_dec["Soma"]




# Monta a série do SP500
SP500 = yf.download("^GSPC", start="2021-01-01", end=data_atual)
SP500 = pd.DataFrame(SP500)


# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
resultados_250 = resultados.iloc[-200:]

# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
df3_250 = df3.iloc[-200:]

# Ajuste o DataFrame merged_df para incluir apenas os últimos 200 dias
merged_df_250 = merged_df.iloc[-200:]

# Ajuste o DataFrame SP500_df para incluir apenas os últimos 200 dias
SP500_250 = SP500.iloc[-200:]


# Crie subplots com três linhas (uma para cada gráfico)

# Crie subplots
fig = make_subplots(rows=4, cols=1, shared_xaxes=True)

# Adicione o gráfico de linha do NH_NL_I e do NH_NL_I_Media_Movel na primeira linha
fig.add_trace(
    go.Scatter(
        x=resultados_250.index,
        y=resultados_250["NH_NL_I_Media_Movel_10"],
        mode="lines",
        name="NH NL I",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=resultados_250.index,
        y=resultados_250["NH_NL_I_Media_Movel"],
        mode="lines",
        name="MMA10",
    ),
    row=1,
    col=1,
)
# # Adicione o gráfico de linha da LAD na segunda linha
fig.add_trace(
    go.Scatter(x=df3_250.index, y=df3_250["addc"], mode="lines", name="LAD"),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(x=df3_250.index, y=df3_250["addc_MMA"], mode="lines", name="MMA21"),
    row=2,
    col=1,
)
# Adicione o gráfico do somatório de sobrecomprados e sobrevendidos na terceira linha
fig.add_trace(
    go.Scatter(
        x=merged_df_250.index,
        y=merged_df_250["RSI_gt_70"],
        mode="lines",
        name="IFR > 70",
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=merged_df_250.index,
        y=merged_df_250["RSI_lw_30"],
        mode="lines",
        name="IFR < 30",
    ),
    row=3,
    col=1,
)


# # Adicione o gráfico de linha do SP500 na quarta linha
fig.add_trace(
    go.Scatter(
        x=SP500_250.index, y=SP500_250["Adj Close"], mode="lines", name="S&P 500"
    ),
    row=4,
    col=1,
)
# Adicione as anotações de fonte aos subplots
fig.add_annotation(
    text="Fonte: Yahoo! Finance, Slickcharts e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray"),
)


# Atualize os layouts dos subplots
fig.update_layout(
    title_text=f"Análise de Amplitude | Ponderada pelo Peso de Cada Ação no Índice | S&P 500 - {dt}",
    showlegend=True,
    xaxis_rangeslider_visible=False,
)
fig.update_yaxes(title_text="LAD vs. MMA21", row=2, col=1)
fig.update_yaxes(title_text="NH NL I vs. MMA10", row=1, col=1)
fig.update_yaxes(title_text="Somatória do IFR", row=3, col=1)
#fig.update_yaxes(title_text="Nova Amplitude", row=4, col=1)
#fig.update_yaxes(title_text="McClellan Oscillator", row=5, col=1)
fig.update_yaxes(title_text="S&P 500", row=4, col=1)
fig.update_xaxes(title_text="Data", row=6, col=1)
# Exiba os subplots
fig.show()


print("##################################")
#Imprime o nome dos indicadores de amplitude
nomes_indicadores = ["New Highs-New Lows Index", "Linha de Avanço e Declinio (LAD)", "Somatória dos IFRs", "Nova Amplitude", "McClellan Oscillator"]

# Imprimir os nomes dos indicadores de amplitude
for indicador in nomes_indicadores:
    print(indicador)