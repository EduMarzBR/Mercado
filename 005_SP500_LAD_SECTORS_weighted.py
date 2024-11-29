import yfinance as yf
import pandas as pd
from pandas_datareader import data as pdr
import requests
from bs4 import BeautifulSoup
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")


def get_sector(ticker):
    return yf.Ticker(ticker).info["sector"]


# Listar as ações que fazem parte do S&P500

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
acoesSP500 = df["Symbol"]
acoesSP500 = acoesSP500[~acoesSP500.isin(["2481632D","2443527D","AMTM"])].tolist()

pesos = df["Weight"].astype(float)/100


yf.set_tz_cache_location("custom/cache/location")

data_atual = datetime.date.today()
dt = data_atual.strftime("%d/%m/%Y")


# Indenticar o setor das ações que fazem parte do S&P500

eq_sector = pd.DataFrame()


eq_sector["Symbol"] = acoesSP500
eq_sector["Peso"] = pesos

for r in range(0, len(acoesSP500)):
    setor = get_sector(acoesSP500[r])
    eq_sector.loc[r, "Setor"] = setor

quantidade = eq_sector.groupby("Setor").count()

print(quantidade)

setores = eq_sector["Setor"].unique()

lad = []

mma = 21
for setor in setores:
    lista_setor = eq_sector.loc[eq_sector["Setor"] == setor]
    acoes = lista_setor["Symbol"]
    pesos = lista_setor["Peso"]
    # Calcular os avanços e declínios de cada dia
    dfs_temp = []

    for acao, peso in zip(acoes, pesos):
        if acao == "2318605D":
            acao = "BG"

        acn = yf.download(acao, start="2023-01-01", end=data_atual)

        # Calcular a Linha de Avaço e Declínio do SP500
        df1 = pd.DataFrame(acn)

        condition_1 = df1["Adj Close"].diff()

        df1["signal"] = condition_1 > 0

        # Armazenar o DataFrame temporário na lista
        dfs_temp.append(df1["signal"].astype(int).apply(lambda x: x * peso if x==1 else -peso))

    # Concatenar os DataFrames temporários para criar df3
    df3 = pd.concat(dfs_temp, axis=1)

    # Substituir 0 por -1 em todo o DataFrame
#    df3.replace(0, -1, inplace=True)

    # Calcular a coluna "Soma" usando a vetorização
    df3["Soma"] = df3.sum(axis=1)

    # Calcular a coluna "addc", LAD
    df3["addc1"] = df3["Soma"].cumsum()

    df3["addc"] = df3["addc1"].ewm(span=7, adjust=False).mean()

    # Calcular a média móvel de addc, LAD
    df3["addc_MMA"] = df3["addc"].rolling(window=mma).mean()
    df3.rename(
        columns={"addc": f"addc_{setor}", "addc_MMA": f"addc_MMA_{setor}"}, inplace=True
    )

    # Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
    df3_250 = df3
    lad.append(df3_250[[f"addc_{setor}", f"addc_MMA_{setor}"]])

lad_all = pd.concat(lad, axis=1)

lad_all = pd.DataFrame(lad_all)

# Calcular a LAD do SP500
dfs_temp1 = []
for acao in acoesSP500:
    if acao == "2318605D":
        acao = "BG"

    acn = yf.download(acao, start="2023-01-01", end=data_atual)

    # Calcular a Linha de Avaço e Declínio do SP500
    df1 = pd.DataFrame(acn)

    condition_1 = df1["Adj Close"].diff()

    df1["signal"] = condition_1 > 0

    # Armazenar o DataFrame temporário na lista
    dfs_temp1.append(df1["signal"].astype(int).apply(lambda x: x * peso if x==1 else -peso))

# Concatenar os DataFrames temporários para criar df3
df4 = pd.concat(dfs_temp1, axis=1)

# Substituir 0 por -1 em todo o DataFrame
#df4.replace(0, -1, inplace=True)

# Calcular a coluna "Soma" usando a vetorização
df4["Soma"] = df4.sum(axis=1)

# Calcular a coluna "addc", LAD
df4["addc1"] = df4["Soma"].cumsum()

df4["addc"] = df4["addc1"].ewm(span=9, adjust=False).mean()

# Calcular a média móvel de addc, LAD
df4["addc_MMA"] = df4["addc"].rolling(window=mma).mean()


df4_250 = df4


# Crie subplots com três linhas (uma para cada gráfico)

fig = make_subplots(rows=6, cols=2, shared_xaxes=True)

# # Adicione o gráfico de linha da LAD S&P500
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc"],
        mode="lines",
        name="LAD S&P500",
        line=dict(color="blue"),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=1,
    col=1,
)
# # Adicione o gráfico de linha da LAD Basic Materials
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Basic Materials"],
        mode="lines",
        name="LAD Materiais Básicos",
        line=dict(color="#FFD700"),
    ),
    row=1,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Basic Materials"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=1,
    col=2,
)
# # Adicione o gráfico de linha da LAD Communication Services
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Communication Services"],
        mode="lines",
        name="LAD Comunicação",
        line=dict(color="#00FF00"),
    ),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Communication Services"],
        mode="lines",
        name=f"MMA{mma} IBOV",
        line=dict(color="red"),
    ),
    row=2,
    col=1,
)
# # Adicione o gráfico de linha da LAD Consumer Cyclical
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Consumer Cyclical"],
        mode="lines",
        name="LAD Cons. Cíclico",
        line=dict(color="#00FFFF"),
    ),
    row=2,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Consumer Cyclical"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=2,
    col=2,
)
# # Adicione o gráfico de linha da LAD Consumer Defensive
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Consumer Defensive"],
        mode="lines",
        name="LAD Cons. Não Cíclico",
        line=dict(color="#000000"),
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Consumer Defensive"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=3,
    col=1,
)
# # Adicione o gráfico de linha da LAD Energy
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Energy"],
        mode="lines",
        name="LAD Energia",
        line=dict(color="#A52A2A"),
    ),
    row=3,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Energy"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=3,
    col=2,
)
# # Adicione o gráfico de linha da LAD Financial Services
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Financial Services"],
        mode="lines",
        name="LAD Financeiro",
        line=dict(color="#FFA500"),
    ),
    row=4,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Financial Services"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=4,
    col=1,
)
# # Adicione o gráfico de linha da LAD Healthcare
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Healthcare"],
        mode="lines",
        name="LAD Saúde",
        line=dict(color="#800080"),
    ),
    row=4,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Healthcare"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=4,
    col=2,
)
# # Adicione o gráfico de linha da LAD Industrials
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Industrials"],
        mode="lines",
        name="LAD Industrial",
        line=dict(color="#00FF00"),
    ),
    row=5,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Industrials"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=5,
    col=1,
)
# # Adicione o gráfico de linha da LAD Real Estate
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Real Estate"],
        mode="lines",
        name="LAD Imoveis",
        line=dict(color="#808000"),
    ),
    row=5,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Real Estate"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=5,
    col=2,
)
# # Adicione o gráfico de linha da LAD Technology
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Technology"],
        mode="lines",
        name="LAD Tecnologia",
        line=dict(color="#87CEEB"),
    ),
    row=6,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Technology"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=6,
    col=1,
)
# # Adicione o gráfico de linha da LAD Utilities
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_Utilities"],
        mode="lines",
        name="LAD Utilidades Públicas",
        line=dict(color="#C0C0C0"),
    ),
    row=6,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=lad_all.index,
        y=lad_all["addc_MMA_Utilities"],
        mode="lines",
        name=f"MMA{mma}",
        line=dict(color="red"),
    ),
    row=6,
    col=2,
)


fig.add_annotation(
    text="Fonte: Yahoo! Finance, Slickcharts e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray"),
)


# Atualize as cores 'cor1' e 'cor2' com as cores desejadas, por exemplo, 'blue' e 'red'
fig.update_traces(marker=dict(size=10))
# Atualize os layouts dos subplots
fig.update_layout(
    title_text=f"Linhas de Avanço e Declínio Setoriais | Ponderadas pelo Peso de Cada Ação no Índice | S&P 500 - {dt}",
    title_font=dict(size=20),
)
fig.update_yaxes(title_text="SPX", row=1, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Mat. Básicos", row=1, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Comunicação", row=2, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Cons. Cíclico", row=2, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Cons. Não Cíclico", row=3, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Energia", row=3, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Financeiro", row=4, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Saúde", row=4, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Industrial", row=5, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Imoveis", row=5, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Tecnologia", row=6, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Util. Públicas", row=6, col=2, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=6, col=1, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=6, col=2, title_font=dict(size=16))
fig.update_legends(font=dict(size=15))
fig.update_annotations(
    dict(
        xref="paper",
        yref="paper",
        x=0,
        y=-0.1,
    )
)


# Exiba os subplots
fig.show()


# Situação dos setores que compõem o S&P 500


def situacao(lad, mma):
    if (lad_all[lad].iloc[-1] - lad_all[mma].iloc[-1]) / abs(
        lad_all[mma].iloc[-1]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (lad_all[lad].iloc[-1] - lad_all[mma].iloc[-1]) / abs(
            lad_all[mma].iloc[-1]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


def situacao_anterior(lad, mma):
    if (lad_all[lad].iloc[-2] - lad_all[mma].iloc[-2]) / abs(
        lad_all[mma].iloc[-2]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (lad_all[lad].iloc[-2] - lad_all[mma].iloc[-2]) / abs(
            lad_all[mma].iloc[-2]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


def situacao_index(lad, mma):
    if (df4_250[lad].iloc[-1] - df4_250[mma].iloc[-1]) / abs(
        df4_250[mma].iloc[-1]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (df4_250[lad].iloc[-1] - df4_250[mma].iloc[-1]) / abs(
            df4_250[mma].iloc[-1]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


sit_index = situacao_index("addc", "addc_MMA")

sit_ant_mat_basicos = situacao_anterior(
    "addc_Basic Materials", "addc_MMA_Basic Materials"
)
sit_mat_basicos = situacao("addc_Basic Materials", "addc_MMA_Basic Materials")

sit_ant_serv_comunicao = situacao_anterior(
    "addc_Communication Services", "addc_MMA_Communication Services"
)
sit_serv_comunicao = situacao(
    "addc_Communication Services", "addc_MMA_Communication Services"
)

sit_ant_cons_disc = situacao_anterior(
    "addc_Consumer Cyclical", "addc_MMA_Consumer Cyclical"
)
sit_cons_disc = situacao("addc_Consumer Cyclical", "addc_MMA_Consumer Cyclical")

sit_ant_cons_basico = situacao_anterior(
    "addc_Consumer Defensive", "addc_MMA_Consumer Defensive"
)
sit_cons_basico = situacao("addc_Consumer Defensive", "addc_MMA_Consumer Defensive")

sit_ant_energia = situacao_anterior("addc_Energy", "addc_MMA_Energy")
sit_energia = situacao("addc_Energy", "addc_MMA_Energy")

sit_ant_serv_financeiros = situacao_anterior(
    "addc_Financial Services", "addc_MMA_Financial Services"
)
sit_serv_financeiros = situacao(
    "addc_Financial Services", "addc_MMA_Financial Services"
)

sit_ant_saude = situacao_anterior("addc_Healthcare", "addc_MMA_Healthcare")
sit_saude = situacao("addc_Healthcare", "addc_MMA_Healthcare")

sit_ant_industrial = situacao_anterior("addc_Industrials", "addc_MMA_Industrials")
sit_industrial = situacao("addc_Industrials", "addc_MMA_Industrials")

sit_ant_imoveis = situacao_anterior("addc_Real Estate", "addc_MMA_Real Estate")
sit_imoveis = situacao("addc_Real Estate", "addc_MMA_Real Estate")

sit_ant_tecnologia = situacao_anterior("addc_Technology", "addc_MMA_Technology")
sit_tecnologia = situacao("addc_Technology", "addc_MMA_Technology")

sit_ant_util_pub = situacao_anterior("addc_Utilities", "addc_MMA_Utilities")
sit_util_pub = situacao("addc_Utilities", "addc_MMA_Utilities")


sit_lad = [
    sit_mat_basicos,
    sit_serv_comunicao,
    sit_cons_disc,
    sit_cons_basico,
    sit_energia,
    sit_serv_financeiros,
    sit_saude,
    sit_industrial,
    sit_imoveis,
    sit_tecnologia,
    sit_util_pub,
]

sit_ant_lad = [
    sit_ant_mat_basicos,
    sit_ant_serv_comunicao,
    sit_ant_cons_disc,
    sit_ant_cons_basico,
    sit_ant_energia,
    sit_ant_serv_financeiros,
    sit_ant_saude,
    sit_ant_industrial,
    sit_ant_imoveis,
    sit_ant_tecnologia,
    sit_ant_util_pub,
]

setores = [
    "Basic Materials",
    "Communication Services",
    "Consumer Cyclical",
    "Consumer Defensive",
    "Energy",
    "Financial Services",
    "Healthcare",
    "Industrials",
    "Real Estate",
    "Technology",
    "Utilities",
]

sit_positivo = sit_lad.count("Positivo")
sit_negativo = sit_lad.count("Negativo")
sit_neutro = sit_lad.count("Neutro")

sit_total = sit_positivo + sit_negativo + sit_neutro
sit_positivo_perc = (sit_positivo / sit_total) * 100
sit_negativo_perc = (sit_negativo / sit_total) * 100
sit_neutro_perc = (sit_neutro / sit_total) * 100

print(f"Linhas de Avanço e Declínio (LAD) | S&P 500 e Setores {dt}:")
print(f"")
print(f"$SP500 - S&P 500 Index - {sit_index}")
print(f"Materiais Básicos - {sit_mat_basicos}")
print(f"Comunicação - {sit_serv_comunicao}")
print(f"Consumo Cíclico - {sit_cons_disc}")
print(f"Consumo Não Cíclico - {sit_cons_basico}")
print(f"Energia - {sit_energia}")
print(f"Financeiro - {sit_serv_financeiros}")
print(f"Saúde - {sit_saude}")
print(f"Industria - {sit_industrial}")
print(f"Imóveis - {sit_imoveis}")
print(f"Tecnologia - {sit_tecnologia}")
print(f"Utilidades Públicas - {sit_util_pub}")
print(f"")
print(f"")
print(f"Mudanças nas LADs:")
print(f"")
# Verifica se houve alguma mudanças na situação das LADs
setor_chg = []
for setor, lad, lad_ant in zip(setores, sit_lad, sit_ant_lad):
    if lad != lad_ant:
        print(f"{setor} | {lad_ant} para {lad}")
        setor_chg.append(setor)
print(f"")
if len(setor_chg) == 0:
    print(f"Nenhuma mudança nas LADs.")
print(f"")
print(f"Situação Geral:")
print(f"")
print(f"LADs Positivas: {sit_positivo} - {sit_positivo_perc:.2f}%")
print(f"LADs Negativas: {sit_negativo} - {sit_negativo_perc:.2f}%")
print(f"LADs Neutras: {sit_neutro} - {sit_neutro_perc:.2f}%")

print(f"")
print(f"O que é a LAD?")
print(
    f"A Linha de Avanço e Declínio (LAD) é uma ferramenta utilizada na análise técnica para avaliar a saúde geral do "
    f"mercado de ações. Ela compara o número de ações que estão em alta (avanço) com o número de ações que estão em "
    f"baixa (declínio) durante um determinado período. Neste estudo, o período é diário. Essa análise é comumente "
    f"aplicada ao mercado amplo, representado por índices, como o índice Brasil Amplo (IBRA) no Brasil ou o S&P 500 "
    f"nos Estados Unidos."
)
print(f"")
print(
    f"Se a Linha de Avanço estiver subindo, isso sugere que há mais ações em alta do que em baixa, indicando um "
    f"mercado mais forte. Por outro lado, se a Linha de Declínio estiver dominando, isso pode indicar fraqueza no "
    f"mercado."
)
print(f"")
print(
    f"A análise da Linha de Avanço e Declínio é frequentemente usada para identificar divergências entre o movimento "
    f"dos preços e a tendência subjacente do mercado, ajudando os investidores a tomarem decisões informadas sobre a "
    f"direção potencial do mercado de ações."
)
