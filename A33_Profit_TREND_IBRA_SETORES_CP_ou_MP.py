import glob
import os
import pandas as pd
import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from B3_D01_Setores import setores
import streamlit as st


# streamlit run C:\Users\armen\PycharmProjects\Profit\A33_Profit_TREND_IBRA_SETORES_CP_ou_MP.py


def esquerda(texto, num_caracteres):
    return texto[:num_caracteres]


# pergunta qual o índice que vc quer
ind = None

while ind not in [1, 2]:
    ind = int(input("Escolha os seguintes índices: 1 - IBOV, 2 - IBRA: "))

    if ind == 1:
        ind1 = "IBOV"
    elif ind == 2:
        ind1 = "IBRA"
    else:
        print("Escolha inválida. Por favor, escolha 1 ou 2.")

# pergunta o time frame que vc quer

tfi = None


while tfi not in [1, 2]:
    tfi = int(input("Escolha os seguintes time frames: 1 - Diário, 2 - Semanal: "))

    if tfi == 1:
        tf = "Diária"
        tf1 = "Diário"
        tf2 = "CURTO PRAZO"
    elif tfi == 2:
        tf = "Semanal"
        tf1 = "Semanal"
        tf2 = "MÉDIO PRAZO"
    else:
        print("Escolha inválida. Por favor, escolha 1 ou 2.")


mma = 30

# Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")


# Carregar a lista de ativo do IBRA

list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/{ind1}/*"
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

# Carregar a lista de ações da B3 com os seus respectivos setores
setores = pd.DataFrame(setores())
# Mudar o nome das colunas para coincidir com o nome da coluna na outra lista e assim juntar as duas listas
setores = setores.rename(columns={"Código": "Cod. Emp."})

df["Cod. Emp."] = df["Código"].apply(esquerda, args=(4,))
# Junta a lista de ações do IBRA com a lista de ações com os seus respectivos setores
df = pd.merge(df, setores, on="Cod. Emp.", how="left")
df = df.drop(columns=["Setor_x", "Empresa", "Segmento"])

# Criar listas com as ações de cada setor
setores_lista = df["Setor_y"].dropna().unique()

lad = []
# Cria lista vazia para armazenar as tendências de alta e baixa no curto  prazo para cada dia
tendencias = []
tendencias_ant = []
dia = -2
for setor in setores_lista:
    lista_setor = df.loc[df["Setor_y"] == setor]
    acoes = lista_setor["Código"]
    # Calcular os avanços e declínios de cada dia
    tendencia = []
    tendencia_ant = []
    for acao in acoes:
        acn = pd.read_csv(
            f"C:/Users/armen/OneDrive/Estratégias/Base/{tf}/"
            + acao
            + f"_B_0_{tf1}.csv",
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

        df0 = pd.DataFrame(acn)
        df0["Data"] = pd.to_datetime(df0["Data"], format="%d/%m/%Y")
        df0 = df0.sort_values(by=["Data"], ascending=True)
        df0.set_index("Data", inplace=True)

        df1 = pd.DataFrame(acn)
        df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")
        df1 = df1.sort_values(by=["Data"], ascending=True)
        df1.set_index("Data", inplace=True)

        # Calcular a tendência dos ativos

        df0["mme9"] = df0["Fechamento"].ewm(span=9, adjust=True).mean()
        df0["mme21"] = df0["Fechamento"].ewm(span=21, adjust=True).mean()

        if df0["Fechamento"].iloc[-1] > df0["mme21"].iloc[-1] and df0["mme9"].iloc[-1] > df0["mme21"].iloc[-1]:
            tendencia.append([f"{acao}", setor, "Alta"])
        elif df0["Fechamento"].iloc[-1] < df0["mme21"].iloc[-1] and df0["mme9"].iloc[-1] < df0["mme21"].iloc[-1]:
            tendencia.append([f"{acao}", setor, "Baixa"])
        else:
            tendencia.append([f"{acao}", setor, "Neutra"])

        if df0["Fechamento"].iloc[dia] > df0["mme21"].iloc[dia] and df0["mme9"].iloc[dia] > df0["mme21"].iloc[dia]:
            tendencia_ant.append([f"{acao}", setor, "Alta"])
        elif df0["Fechamento"].iloc[dia] < df0["mme21"].iloc[dia] and df0["mme9"].iloc[dia] < df0["mme21"].iloc[dia]:
            tendencia_ant.append([f"{acao}", setor, "Baixa"])
        else:
            tendencia_ant.append([f"{acao}", setor, "Neutra"])

    df_tendencias = pd.DataFrame(tendencia)
    df_tendencias = df_tendencias.rename(
        columns={0: "Código", 1: "Setor", 2: "Tendência"}
    )

    tendencias.append(df_tendencias[["Código", "Setor", "Tendência"]])

    df_tendencias_ant = pd.DataFrame(tendencia_ant)
    df_tendencias_ant = df_tendencias_ant.rename(
        columns={0: "Código", 1: "Setor", 2: "Tendência"}
    )

    tendencias_ant.append(df_tendencias_ant[["Código", "Setor", "Tendência"]])


tend_all = pd.concat(tendencias)
tend_all_ant = pd.concat(tendencias_ant)


perct_trend_high = []
perct_trend_high_ant = []
print(
    f"**Ações do ${ind1} em tendência de alta no {tf2}, agrupadas por setor - {dt}**"
)
for setor in setores_lista:
    list_setor_alta = tend_all[
        (tend_all["Setor"] == setor) & (tend_all["Tendência"] == "Alta")
    ]
    list_setor_alta = list_setor_alta["Código"].tolist()
    lista_todo_setor = tend_all[(tend_all["Setor"] == setor)]["Código"].tolist()
    perct_tend_alta = round((len(list_setor_alta) / len(lista_todo_setor)) * 100, 2)
    perct_trend_high.append(perct_tend_alta)
    print("")
    print(f"**{setor}**")
    print(f"{perct_tend_alta} % do setor em tendência Alta: {list_setor_alta}")
    print(
        f"De {len(lista_todo_setor)} ativos, {len(list_setor_alta)} ativos em tendência Alta"
    )

    # Dados do dia anterior
    list_setor_alta_ant = tend_all_ant[
        (tend_all_ant["Setor"] == setor) & (tend_all_ant["Tendência"] == "Alta")
    ]
    list_setor_alta_ant = list_setor_alta_ant["Código"].tolist()
    lista_todo_setor_ant = tend_all_ant[(tend_all_ant["Setor"] == setor)][
        "Código"
    ].tolist()
    perct_tend_alta_ant = round(
        (len(list_setor_alta_ant) / len(lista_todo_setor_ant)) * 100, 2
    )
    perct_trend_high_ant.append(perct_tend_alta_ant)
    if perct_tend_alta > perct_tend_alta_ant:
        print(
            f"O percentual de ativos em tendência Alta subiu de {perct_tend_alta_ant}% para {perct_tend_alta}%"
        )
    elif perct_tend_alta < perct_tend_alta_ant:
        print(
            f"O percentual de ativos em tendência Alta caiu de {perct_tend_alta_ant}% para {perct_tend_alta}%"
        )
    else:
        print("Não houve mudança no percentual de ativos em tendência Alta")


def create_gauge(value, title):
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            gauge=dict(
                axis=dict(range=[None, 100]),
                bar=dict(color="rgba(200, 128, 255, 0.7)"),  # Azul mais claro
                steps=[
                    {"range": [0, 25], "color": "rgba(0, 128, 255, 0.3)"},
                    {"range": [25, 50], "color": "rgba(0, 128, 255, 0.5)"},
                    {"range": [50, 75], "color": "rgba(0, 128, 255, 0.7)"},
                    {"range": [75, 100], "color": "rgba(0, 128, 255, 0.9)"},
                ],
            ),
        )
    )

    return fig


def main():
    st.set_page_config(layout="wide")  # Configuração para ampliar o layout

    st.title(f"Tendências de Alta - Setores do {ind1}")

    # Criar 10 velocímetros com valores aleatórios
    velocidades = perct_trend_high

    # Criar 2 linhas com 5 colunas cada
    col1, col2, col3, col4, col5 = st.columns(5)

    # Adicionar velocímetros em cada coluna na primeira linha
    for i, velocidade, setor in zip(range(5), velocidades[:5], setores_lista[:5]):
        with locals()[f"col{i + 1}"]:
            st.plotly_chart(
                create_gauge(velocidade, f"{setor}"),
                use_container_width=True,
            )

    # Adicionar uma coluna de espaço entre as duas linhas
    st.write(
        "<style>div.row-widget.stHorizontal { flex-wrap: wrap; }</style>",
        unsafe_allow_html=True,
    )

    # Criar a segunda linha com 5 colunas
    col6, col7, col8, col9, col10 = st.columns(5)

    # Adicionar velocímetros em cada coluna na segunda linha
    for i, velocidade, setor in zip(range(5), velocidades[5:], setores_lista[5:]):
        with locals()[f"col{i + 6}"]:
            st.plotly_chart(
                create_gauge(velocidade, f"{setor}"),
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
