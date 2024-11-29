import glob
import os
import pandas as pd
import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import warnings


# streamlit run C:\Users\armen\PycharmProjects\Profit\A39_Profit_MACD_Streamlit.py

# Permite que o usuário escolha entre o IBOV, IBRA, BDRX, ICON, IDIV, IEEX, IFIX, IFNC, IMAT, IMOB, INDX, MLCX, SMLL, UTIL

warnings.filterwarnings("ignore")
# Exibe a lista de códigos de índices
print("Escolha um índice:")
print("1 - IBOV")
print("2 - IBRA")
print("3 - BDRX")
print("4 - ICON")
print("5 - IDIV")
print("6 - IEEX")
print("7 - IFIX")
print("8 - IFNC")
print("9 - IMAT")
print("10 - IMOB")
print("11 - INDX")
print("12 - MLCX")
print("13 - SMLL")
print("14 - UTIL")

# Solicita ao usuário que digite o número correspondente ao índice desejado
codigo = int(input("Digite o número do índice desejado: "))

# Dicionário que mapeia códigos para os nomes dos índices
indices = {
    1: "IBOV",
    2: "IBRA",
    3: "BDRX",
    4: "ICON",
    5: "IDIV",
    6: "IEEX",
    7: "IFIX",
    8: "IFNC",
    9: "IMAT",
    10: "IMOB",
    11: "INDX",
    12: "MLCX",
    13: "SMLL",
    14: "UTIL",
}

# Verifica se o código digitado pelo usuário está no dicionário
if codigo in indices:
    indice = indices[codigo]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")

# Agora, a variável "indice" contém o código selecionado (ou é None se o código for inválido)


list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*"
)  # * means all if need specific format then *.csv
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
acoes = df["Código"]


# Diretório onde os arquivos CSV estão localizados
diretorio = "C:/Users/armen/OneDrive/Estratégias/Base/Diária/"


# Criar um DataFrame vazio para armazenar os resultados
resultados = pd.DataFrame()


# Calcular a Linha de Avaço e Declínio e de Somatória do IFR IBRA
MACD_resultados = []
MACD_comprados = []
MACD_vendidos = []
for x in acoes:
    acn = pd.read_csv(
        "C:/Users/armen/OneDrive/Estratégias/Base/Diária/" + x + "_B_0_Diário.csv",
        sep=";",
        encoding="ISO-8859-1",
        skiprows=0,
        skipfooter=2,
        engine="python",
        thousands=".",
        decimal=",",
        header=0,
        index_col=False,
    )
    df1 = pd.DataFrame(acn)
    df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")

    df1 = df1.sort_values(by=["Data"], ascending=True)
    df1["MACD"], df1["MACD_Signal"], _ = talib.MACD(
        df1["Fechamento"], fastperiod=12, slowperiod=26, signalperiod=9
    )
    df1["Compra"] = (df1["MACD"] > df1["MACD_Signal"]) & (df1["MACD"] > 0)
    df1["Venda"] = (df1["MACD"] < df1["MACD_Signal"]) & (df1["MACD"] < 0)
    pd.set_option("future.no_silent_downcasting", True)
    df1.replace(True, 1, inplace=True)
    df1.replace(False, 0, inplace=True)

    MACD_resultados.append(df1[["Data", "Compra", "Venda"]])

    try:
        if df1["Compra"].iloc[-1] == 1:
            MACD_comprados.append(f"{x}")
        if df1["Venda"].iloc[-1] == 1:
            MACD_vendidos.append(f"{x}")
    except:
        pass


# Concatenar os resultados de todos os ativos


merged_df = pd.concat(MACD_resultados)
merged_df["Data"] = pd.to_datetime(merged_df["Data"], format="%d/%m/%Y")

merged_df = merged_df.sort_values(by=["Data"], ascending=True)
merged_df.set_index("Data", inplace=True)
merged_df = merged_df.groupby(merged_df.index).sum()


# Monta a série do IBRA
IBRA = pd.read_csv(
    "C:/Users/armen/OneDrive/Estratégias/Base/Diária/IBRA_B_0_Diário.csv",
    sep=";",
    encoding="ISO-8859-1",
    skiprows=0,
    skipfooter=2,
    engine="python",
    thousands=".",
    decimal=",",
    header=0,
    index_col=False,
)
IBRA = pd.DataFrame(IBRA)
IBRA["Data"] = pd.to_datetime(IBRA["Data"], format="%d/%m/%Y")
IBRA.drop(
    columns=["Ativo", "Abertura", "Máximo", "Mínimo", "Volume", "Quantidade"],
    inplace=True,
)
IBRA = IBRA.sort_values(by=["Data"], ascending=True)
IBRA.set_index("Data", inplace=True)


# Ajuste o DataFrame RSI_resultados para incluir apenas os últimos 200 dias
merged_df_250 = merged_df.iloc[-200:]

# Ajuste o DataFrame IBRA_df para incluir apenas os últimos 200 dias
IBRA_250 = IBRA.iloc[-200:]

# Traz a data atual

data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")

# Crie subplots com três linhas (uma para cada gráfico)


fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3]
)

# Adicione o gráfico de linha do RSI na terceira linha
fig.add_trace(
    go.Scatter(
        x=merged_df_250.index,
        y=merged_df_250["Compra"],
        mode="lines",
        name="Comprados",
        line=dict(color="#87CEEB"),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=merged_df_250.index,
        y=merged_df_250["Venda"],
        mode="lines",
        name="Vendidos",
        line=dict(color="red"),
    ),
    row=1,
    col=1,
)

# # Adicione o gráfico de linha do IBRA na quarta linha
fig.add_trace(
    go.Scatter(x=IBRA_250.index, y=IBRA_250["Fechamento"], mode="lines", name="IBRA"),
    row=2,
    col=1,
)
# Adicione as anotações de fonte aos subplots


# Atualizar layout
fig.update_layout(
    title_text=f"Ações do {indice} compradas e vendidas pelo MACD vs. {indice} - {dt}",
    title_font=dict(size=20),
    legend=dict(font=dict(size=19)),  # Para ocultar a legenda duplicada
)


fig.add_annotation(
    text="Fonte: Nelogica e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray"),
)


# Atualize os layouts dos subplots

fig.update_yaxes(
    title_text="Compradas e vendidas", row=1, col=1, title_font=dict(size=16)
)
fig.update_yaxes(title_text=f"{indice}", row=2, col=1, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=2, col=1, title_font=dict(size=16))
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
st.plotly_chart(fig)
print("")
print(f"**Ações do ${indice} compradas e vendidas pelo MACD - {dt}**")
print("")
print(f"Ações compradas pelo MACD ({len(MACD_comprados)} ativos): {MACD_comprados}")
print("")
print(f"Ações vendidas pelo MACD ({len(MACD_vendidos)} ativos): {MACD_vendidos}")
print("")
print(
    "Compradas: são as ações cuja medida do MACD está acima da medida da sua média móvel e a medida do"
)
print("MACD é maior do que zero.")
print("")
print(
    "Vendidas: são as ações cuja medida do MACD está abaixo da medida da sua média móvel e a medida do MACD é"
)
print("menor do que zero.")
print("")
print("O que é o MACD?")
print("")
print(
    "O MACD (Moving Average Convergence Divergence) é um indicador de análise técnica utilizado para identificar a "
    "força e a direção de uma tendência em um ativo financeiro, como ações, moedas ou commodities. Ele foi "
    "desenvolvido por Gerald Appel e é amplamente utilizado por traders e analistas."
)
print("")
print(
    "O indicador MACD é derivado da diferença entre duas médias móveis exponenciais (MME) de diferentes períodos. "
    "Os componentes principais do MACD são:"
)
print("")
print(
    "Linha MACD (MACD Line): É a diferença entre a MME de curto prazo e a MME de longo prazo. "
    "A fórmula para a Linha MACD é: MACD Line = MME de curto prazo - MME de longo prazo."
)
print("")
print(
    "Linha de Sinal (Signal Line): É uma MME da Linha MACD, geralmente calculada com um período menor. "
    "A fórmula é: Signal Line = MME da Linha MACD."
)
print("")
