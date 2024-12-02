import pandas as pd
from pandas_datareader import data as pdr
import datetime
import yfinance as yf
import talib
import requests
from bs4 import BeautifulSoup
import warnings
import time


warnings.filterwarnings("ignore")
# Registre o tempo de início
tempo_inicio = time.time()
agora = datetime.datetime.now()

print("Inicio: ", agora.strftime("%H:%M:%S"))
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
acoes = df["Symbol"].apply(lambda x: "GEV-WI" if x == "GEVw" else x)
acoes = acoes[~acoes.isin(["2483490D","AMTM-W"])].tolist()

empresas = df["Empresa"]


yf.set_tz_cache_location("custom/cache/location")

data_atual = datetime.date.today()
dt = data_atual.strftime("%d/%m/%Y")


def verificar_tendencia(serie):
    tendencia = ""
    dias_sequencia = 1

    for i in range(len(serie) - 1, 1, -1):
        if serie.iloc[i] > serie.iloc[i - 1] > serie.iloc[i - 2]:
            tendencia = "alta"
            dias_sequencia += 1
        elif serie.iloc[i] < serie.iloc[i - 1] < serie.iloc[i - 2]:
            tendencia = "baixa"
            dias_sequencia += 1
        else:
            break
    antes = serie.iloc[-dias_sequencia - 1]
    depois = serie.iloc[-1]
    resultado = round(((depois - antes) / antes) * 100, 2)
    return tendencia, dias_sequencia, resultado


# Função para verificar se há uma sequência de 5 dias de altas
def sequencia_altas(preco, dias_sequencia):
    return all(preco.iloc[i] < preco.iloc[i + 1] for i in range(dias_sequencia))


def sequencia_baixas(preco, dias_sequencia):
    return all(preco.iloc[i] > preco.iloc[i + 1] for i in range(dias_sequencia))


# Função para contar quantas vezes o preço continua em alta ou cai após uma sequência de 5 dias de altas
def contar_tendencias_alta(serie, dias_sequencia, dias_total):
    cont_continua_alta = 0
    cont_cai = 0

    for i in range(len(serie) - dias_total):
        if sequencia_altas(serie[i : i + dias_total], dias_sequencia):
            if serie.iloc[i + dias_sequencia] < serie.iloc[i + dias_total]:
                cont_continua_alta += 1
            else:
                cont_cai += 1

    return cont_continua_alta, cont_cai


def contar_tendencias_baixa(serie, dias_sequencia, dias_total):
    cont_continua_baixa = 0
    cont_sobe = 0

    for i in range(len(serie) - dias_total):
        if sequencia_baixas(serie[i : i + dias_total], dias_sequencia):
            if serie.iloc[i + dias_sequencia] > serie.iloc[i + dias_total]:
                cont_continua_baixa += 1
            else:
                cont_sobe += 1

    return cont_continua_baixa, cont_sobe


print("")
print("")

# Iterar sobre cada ação
adj_close = pd.DataFrame()
ifr = pd.DataFrame()

for acao in acoes:
    if acao == "2318605D":
        acao = "BG"

    df = yf.download(acao, start="2020-01-01", end=data_atual)
    df = pd.DataFrame(df)
    df["IFR"] = talib.RSI(df["Adj Close"], timeperiod=14)

    df = df.rename(columns={"Adj Close": acao, "IFR": f"IFR_{acao}"})
    adj_close = pd.concat([adj_close, df[acao]], axis=1)
    ifr = pd.concat([ifr, df[f"IFR_{acao}"]], axis=1)
adj_close = adj_close.copy()
ifr = ifr.copy()
acoes_s = []

print("'")
print("-" * 60)
for acao, empresa in zip(adj_close.columns, empresas):

    # Verificar a tendência e quantificar a sequência
    tendencia, dias_sequencia, resultado = verificar_tendencia(adj_close[acao])
    dias_total = dias_sequencia + 1
    cont_continua_alta, cont_cai = contar_tendencias_alta(
        adj_close[acao], dias_sequencia, dias_total
    )
    cont_continua_baixa, cont_sobe = contar_tendencias_baixa(
        adj_close[acao], dias_sequencia, dias_total
    )

    dias = 5
    variacao = 10
    if dias_sequencia > dias and tendencia == "alta" and resultado > variacao:
        acoes_s.append(acao)
        print("")
        print(f"Ação: ${acao} ")
        if ifr[f"IFR_{acao}"].iloc[-1] > 70:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrecomprada)")
        elif ifr[f"IFR_{acao}"].iloc[-1] < 30:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrevendida)")
        else:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)}")
        print(f"Está vindo de uma sequência de: {dias_sequencia} dias de {tendencia}")
        print(f"Ganho de: {resultado}%")

        if cont_continua_alta == 0:
            print(
                f"Continua a alta após uma sequência de {dias_sequencia} dias de alta: não aconteceu"
            )
        else:
            print(
                f"Continua a alta após uma sequência de {dias_sequencia} dias de alta: {round(cont_continua_alta/(cont_continua_alta + cont_cai)*100,1)}% das vezes"
            )

        if cont_cai == 0:
            print(
                f"Cai após uma sequência de {dias_sequencia} dias de alta: não aconteceu"
            )
        else:
            print(
                f"Cai após uma sequência de {dias_sequencia} dias de alta: {round(cont_cai/(cont_continua_alta + cont_cai)*100,1)}% das vezes"
            )
        print(
            f"Estudo estatístico realizado nos últimos: {len(adj_close[acao])} pregões"
        )
        print("-" * 60)
    elif dias_sequencia > dias and tendencia == "baixa" and resultado < -variacao:
        acoes_s.append(acao)
        print("")
        print(f"Ação: ${acao}")
        if ifr[f"IFR_{acao}"].iloc[-1] > 70:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrecomprada)")
        elif ifr[f"IFR_{acao}"].iloc[-1] < 30:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrevendida)")
        else:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)}")
        print(f"Está vindo de uma sequência de: {dias_sequencia} dias de {tendencia}")
        print(f"Perda de: {resultado}%")
        if cont_continua_baixa == 0:
            print(
                f"Continua a queda após uma sequência de {dias_sequencia} dias de baixa: não aconteceu"
            )
        else:
            print(
                f"Continua a queda após uma sequência de {dias_sequencia} dias de baixa: {round(cont_continua_baixa/(cont_continua_baixa + cont_sobe)*100,1)}% das vezes"
            )
        if cont_sobe == 0:
            print(f"Sobe após uma sequência de {dias_sequencia} dias de baixa: não aconteceu")
        else:
            print(
                f"Sobe após uma sequência de {dias_sequencia} dias de baixa: {round(cont_sobe/(cont_continua_baixa + cont_sobe)*100,1)}% das vezes"
            )
        print(
            f"Estudo estatístico realizado nos últimos: {len(adj_close[acao])} pregões"
        )
        print("-" * 60)


print("")
print("")
print(
    f"{len(acoes_s)} Ações americanas em sequência de alta ou baixa maiores do que {dias} dias e com variação acima de {variacao}% - {dt}"
)


print("")
print("")
agora = datetime.datetime.now()

print("Fim do programa: ", agora.strftime("%H:%M:%S"))
# Registre o tempo de término
tempo_fim = time.time()

# Calcule o tempo de processamento em segundos
tempo_processamento_segundos = tempo_fim - tempo_inicio

# Calcule o tempo de processamento em minutos
tempo_processamento_minutos = tempo_processamento_segundos / 60

# Imprima o tempo de processamento em minutos
print("Tempo de processamento:", tempo_processamento_minutos, "minutos")