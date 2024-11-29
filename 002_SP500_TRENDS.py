import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import streamlit as st
import plotly.graph_objects as go
import warnings

# streamlit run C:\Users\armen\PycharmProjects\YahooFinance\002_SP500_TRENDS.py
tfi=0

while tfi not in [1, 2]:
    tfi = int(input("Escolha os seguintes time frames: 1 - Diário, 2 - Semanal: "))

    if tfi == 1:
        tf = "1d"
        tf1 = "CURTO PRAZO"
    elif tfi == 2:
        tf = "1wk"
        tf1 = "MÉDIO PRAZO"
    else:
        print("Escolha inválida. Por favor, escolha 1 ou 2.")





warnings.filterwarnings("ignore")


def get_sector(ticker):
    return yf.Ticker(ticker).info["sector"]


# Listar as ações que fazem parte do S&P500

# URL da página da web que contém a tabela
url = "http://www.slickcharts.com/sp500/performance"

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
                coluna1.append(colunas[0].text.strip())
                coluna2.append(colunas[1].text.strip())
                # Substitua os pontos por hifens na coluna3, se houver
                coluna3.append(colunas[2].text.strip().replace(".", "-"))

        # Crie um DataFrame com as colunas extraídas
        df = pd.DataFrame({"Symbol": coluna3, "Empresa": coluna2})

        # Exiba o DataFrame

    else:
        print("Tabela não encontrada na página.")

else:
    print("Falha na solicitação à página da web.")

# Cria uma lista usando a coluna 'Symbol'
acoesSP500 = df["Symbol"]

acoesSP500 = acoesSP500[~acoesSP500.isin(["2481632D","2483490D","AMTM","CAT"])].tolist()







yf.set_tz_cache_location("custom/cache/location")

data_atual = datetime.date.today()
dt = data_atual.strftime("%d/%m/%Y")


# Indenticar o setor das ações que fazem parte do S&P500

eq_sector = pd.DataFrame()
eq_sector["Symbol"] = acoesSP500
for r in range(0, len(acoesSP500)):
    print(acoesSP500[r])
    setor = get_sector(acoesSP500[r])
    eq_sector.loc[r, "Setor"] = setor

quantidade = eq_sector.groupby("Setor").count()

print(quantidade)

setores = eq_sector["Setor"].unique()


tendencias = []
tendencias_ant = []
dia = -2
# Loop pelos setores para descobrir a tendência atual
for setor in setores:
    lista_setor = eq_sector.loc[eq_sector["Setor"] == setor]
    acoes = lista_setor["Symbol"]
    # Calcular os avanços e declínios de cada dia
    tendencia_ant = []
    tendencia = []

    for acao in acoes:
        try:
            if acao == "2318605D":
                acao = "BG"

            acn = yf.download(acao, start="2021-01-01", end=data_atual, interval=tf)

            # Calcular a Linha de Avaço e Declínio do SP500
            df1 = pd.DataFrame(acn)

            df1["mme9"] = df1["Adj Close"].ewm(span=9, adjust=True).mean()
            df1["mme21"] = df1["Adj Close"].ewm(span=21, adjust=True).mean()

            if (
                df1["Adj Close"].iloc[-1] > df1["mme21"].iloc[-1]

            ):
                tendencia.append([f"{acao}", setor, "Alta"])
            elif (
                df1["Adj Close"].iloc[-1] < df1["mme21"].iloc[-1]

            ):
                tendencia.append([f"{acao}", setor, "Baixa"])
            else:
                tendencia.append([f"{acao}", setor, "Neutra"])

            if (
                df1["Adj Close"].iloc[dia] > df1["mme21"].iloc[dia]

            ):
                tendencia_ant.append([f"{acao}", setor, "Alta"])
            elif (
                df1["Adj Close"].iloc[dia] < df1["mme21"].iloc[dia]

            ):
                tendencia_ant.append([f"{acao}", setor, "Baixa"])
            else:
                tendencia_ant.append([f"{acao}", setor, "Neutra"])

        except:
            print(f"Ativo {acao} não encontrado.")

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

# Substituir os nomes dos setores em todo o DataFrame
tend_all.replace("Communication Services", "Comunicações", inplace=True)
tend_all.replace("Consumer Cyclical", "Consumo Cíclico", inplace=True)
tend_all.replace("Consumer Defensive", "Consumo Não Cíclico", inplace=True)
tend_all.replace("Utilities", "Utilidade Pública", inplace=True)
tend_all.replace("Healthcare", "Saúde", inplace=True)
tend_all.replace("Financial Services", "Financeiro", inplace=True)
tend_all.replace("Technology", "Tecnologia", inplace=True)
tend_all.replace("Basic Materials", "Materiais Básicos", inplace=True)
tend_all.replace("Energy", "Energia", inplace=True)
tend_all.replace("Industrials", "Indústria", inplace=True)
tend_all.replace("Real Estate", "Imóveis", inplace=True)

# Substituir os nomes dos setores em todo o DataFrame
tend_all_ant.replace("Communication Services", "Comunicações", inplace=True)
tend_all_ant.replace("Consumer Cyclical", "Consumo Cíclico", inplace=True)
tend_all_ant.replace("Consumer Defensive", "Consumo Não Cíclico", inplace=True)
tend_all_ant.replace("Utilities", "Utilidade Pública", inplace=True)
tend_all_ant.replace("Healthcare", "Saúde", inplace=True)
tend_all_ant.replace("Financial Services", "Financeiro", inplace=True)
tend_all_ant.replace("Technology", "Tecnologia", inplace=True)
tend_all_ant.replace("Basic Materials", "Materiais Básicos", inplace=True)
tend_all_ant.replace("Energy", "Energia", inplace=True)
tend_all_ant.replace("Industrials", "Indústria", inplace=True)
tend_all_ant.replace("Real Estate", "Imóveis", inplace=True)


# Lista os setores depois da substituição dos nomes em inglês para o português
setores = tend_all["Setor"].unique()

perct_trend_high = []
perct_trend_high_ant = []
print(f"**Ações do $SP500 em tendência de alta no {tf1}, agrupadas por setor - {dt}**")
for setor in setores:
    # Dados do dia atual
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

    st.title("Tendências de Alta - Setores do S&P500")

    # Criar 10 velocímetros com valores aleatórios
    velocidades = perct_trend_high

    # Criar 2 linhas com 5 colunas cada
    col1, col2, col3, col4, col5 = st.columns(5)

    # Adicionar velocímetros em cada coluna na primeira linha
    for i, velocidade, setor in zip(range(5), velocidades[:5], setores[:5]):
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
    col6, col7, col8, col9, col10, col11 = st.columns(6)

    # Adicionar velocímetros em cada coluna na segunda linha
    for i, velocidade, setor in zip(range(6), velocidades[5:], setores[5:]):
        with locals()[f"col{i + 6}"]:
            st.plotly_chart(
                create_gauge(velocidade, f"{setor}"),
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
