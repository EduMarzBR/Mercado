import glob
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime




def mme9(data):
    mme9 = data["Fechamento"].ewm(span=9, adjust=False).mean()
    return mme9


def mme21(data):
    mme21 = data["Fechamento"].ewm(span=21, adjust=False).mean()
    return mme21





# Permite que o usuário escolha entre o IBOV, IBRA, BDRX, ICON, IDIV, IEEX, IFIX, IFNC, IMAT, IMOB, INDX, MLCX, SMLL, UTIL

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


df1 = pd.DataFrame(lista)
acoes = df1["Código"]
pesos = df1["Part. (%)"]

df3_alta = pd.DataFrame()
df3_baixa = pd.DataFrame()
arr_alta = []
arr_baixa = []
for acao, peso in zip(acoes, pesos):
    # Lendo o arquivo CSV
    arquivo_csv = (
        f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{acao}_B_0_Diário.csv"
    )
    df = pd.read_csv(
        arquivo_csv,
        sep=";",
        encoding="ISO-8859-1",
        skiprows=0,
        skipfooter=0,
        engine="python",
        thousands=".",
        decimal=",",
        header=0,
        index_col=False,
    )
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
    df = df.sort_values(by=["Data"], ascending=True)
    df = df.set_index("Data")

    df["mme9"] = mme9(df)
    df["mme21"] = mme21(df)


    df[f"arr_alta {acao}"] = ((df["mme9"] > df["mme21"])
        & (df["Fechamento"] > df["mme21"])
    )
    df[f"arr_baixa {acao}"] = ((df["mme9"] < df["mme21"])
        & (df["Fechamento"] < df["mme21"])
    )

    arr_alta.append(df[f"arr_alta {acao}"].astype(int))
    arr_baixa.append(df[f"arr_baixa {acao}"].astype(int))

    df_arr_alta = pd.concat(arr_alta, axis=1)
    df_arr_baixa = pd.concat(arr_baixa, axis=1)

    per_df3 = 21
    df3_alta[f"arr_alta"] = df_arr_alta.sum(axis=1)
    df3_alta[f"arr_alta_media"] = (
        df3_alta["arr_alta"].ewm(span=per_df3, adjust=True).mean()
    )
    df3_alta[f"arr_alta_mm"] = (
        df3_alta["arr_alta_media"].ewm(span=per_df3, adjust=True).mean()
    )
#    df3_alta[f"arr_alta_mm"] = (
#        df3_alta[f"arr_alta_mm1"].ewm(span=per_df3, adjust=True).mean()
#    )

    df3_baixa[f"arr_baixa"] = df_arr_baixa.sum(axis=1)
    df3_baixa[f"arr_baixa_media"] = (
        df3_baixa["arr_baixa"].ewm(span=per_df3, adjust=True).mean()
    )
    df3_baixa[f"arr_baixa_mm"] = (
        df3_baixa["arr_baixa_media"].ewm(span=per_df3, adjust=True).mean()
    )
#    df3_baixa[f"arr_baixa_mm"] = (
#        df3_baixa["arr_baixa_mm1"].ewm(span=per_df3, adjust=True).mean()
#    )

periodo = -200
# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
df4_alta_250 = df3_alta.iloc[periodo:]
df4_baixa_250 = df3_baixa.iloc[periodo:]
saldo = pd.DataFrame()
saldo["Arrancada"] = df4_alta_250["arr_alta"] - df4_baixa_250["arr_baixa"]
per_saldo = 30
saldo["Arrancada media"] = saldo["Arrancada"].ewm(span=per_saldo, adjust=True).mean()




# Monta a série do índice selecionado
ind = pd.read_csv(
    f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{indice}_B_0_Diário.csv",
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
ind = pd.DataFrame(ind)
ind["Data"] = pd.to_datetime(ind["Data"], format="%d/%m/%Y")
ind.drop(
    columns=["Ativo", "Abertura", "Máximo", "Mínimo", "Volume", "Quantidade"],
    inplace=True,
)
ind = ind.sort_values(by=["Data"], ascending=True)
ind.set_index("Data", inplace=True)


ind_250 = ind[periodo:]


# Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")

# Crie subplots com três linhas (uma para cada gráfico)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True)


# # Adicione o gráfico de linha da LAD IBRA
fig.add_trace(
    go.Bar(
        x=saldo.index,
        y=saldo["Arrancada"],
        name="IFT",
        marker=dict(color="#02D9FD"),

    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=saldo.index,
        y=saldo["Arrancada media"],
        mode="lines",
        name=f"MME {per_saldo}",
        line=dict(color="red"),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=ind_250.index,
        y=ind_250["Fechamento"],
        mode="lines",
        name="IBRA",
        line=dict(color="#0089A6"),
    ),
    row=2,
    col=1,
)


fig.add_annotation(
    text="",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray"),
)

# Atualize as cores 'cor1' e 'cor2' com as cores desejadas, por exemplo, 'blue' e 'red'

fig.update_xaxes(
    tickfont=dict(size=18),  # Ajuste o tamanho para o desejado
    row=2, col=1  # Aplique à linha e coluna específicas
)

fig.update_layout(title_text=f"Índice de Força de Tendência {indice} - {dt}", title_font=dict(size=24))
fig.update_yaxes(title_text="IFT", row=1, col=1, title_font=dict(size=20))
fig.update_yaxes(title_text=f"{indice}", row=2, col=1, title_font=dict(size=20))

fig.update_legends(font=dict(size=18))
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
