import pandas as pd
import glob
import os
from pandas_datareader import data as pdr
import yfinance as yf
import datetime

import talib
import warnings
import time
import MetaTrader5 as mt5

# Iniciar a conexão
if not mt5.initialize():
    print("Initialize() failed, error code =", mt5.last_error())
    quit()

# Verificar se a conexão foi bem-sucedida
print("MetaTrader5 version:", mt5.version())
print("")

warnings.filterwarnings("ignore")



# Traz a data atual
data_atual = datetime.datetime.today()
dt = data_atual.strftime("%d/%m/%Y")



# Registre o tempo de início
tempo_inicio = time.time()
agora = datetime.datetime.now()
print("Inicio: ", agora.strftime("%H:%M:%S"))


# Local onde está o arquivo CSV que contém a lista de ações do índice selecionado
list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/IBRA/*"
)  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)
# Carrega o arquivo CSV
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


# Função para verificar se os preços estão vindo de uma sequência maior do que dois dias de alta ou baixa
# Função para verificar se os preços estão vindo de uma sequência de altas ou baixas
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


acoes_s = []


adj_close = pd.DataFrame()
ifr = pd.DataFrame()
periodo = 1000
# Iterar sobre cada ação
for acao in acoes:
    # Carregar o arquivo CSV usando pandas
    df = mt5.copy_rates_from(acao, mt5.TIMEFRAME_D1, datetime.datetime.today(), periodo)
    df = pd.DataFrame(df)
    if df.empty:
        print(f"Erro ao carregar o arquivo {acao}.")
        continue


    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    # Traz o IFR de cada acao
    df["IFR"] = talib.RSI(df["close"], timeperiod=14)
    df_ifr = pd.DataFrame(df["IFR"])
    df = pd.DataFrame(df["close"])
    df = df.rename(columns={"close": f"close_{acao}"})
    adj_close = pd.concat([adj_close, df], axis=1)

    df_ifr = df_ifr.rename(columns={"IFR": f"IFR_{acao}"})
    ifr = pd.concat([ifr, df_ifr], axis=1)

print("")
print("'")
print("-" * 60)

for acao in acoes:
    df = mt5.copy_rates_from(acao, mt5.TIMEFRAME_D1, datetime.datetime.today(), periodo)
    df = pd.DataFrame(df)
    if df.empty:
        continue
    # Verificar a tendência e quantificar a sequência
    tendencia, dias_sequencia, resultado = verificar_tendencia(
        adj_close[f"close_{acao}"]
    )
    dias_total = dias_sequencia + 1
    cont_continua_alta, cont_cai = contar_tendencias_alta(
        adj_close[f"close_{acao}"], dias_sequencia, dias_total
    )
    cont_continua_baixa, cont_sobe = contar_tendencias_baixa(
        adj_close[f"close_{acao}"], dias_sequencia, dias_total
    )

    dias = 5
    variacao = 0
    if dias_sequencia > dias and tendencia == "alta" and resultado > variacao:
        print("")
        acoes_s.append(acao)
        print(f"Ação: ${acao}")
        if ifr[f"IFR_{acao}"].iloc[-1] > 70:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrecomprado)")
        elif ifr[f"IFR_{acao}"].iloc[-1] < 30:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrevendido)")
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
            f"Estudo estatístico realizado nos últimos: {adj_close[f'close_{acao}'].count()} pregões"
        )
        print("-" * 60)
    elif dias_sequencia > dias and tendencia == "baixa" and resultado < -variacao:
        acoes_s.append(acao)
        print("")
        print(f"Ação: ${acao}")
        if ifr[f"IFR_{acao}"].iloc[-1] > 70:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrecomprado)")
        elif ifr[f"IFR_{acao}"].iloc[-1] < 30:
            print(f"IFR: {round(ifr[f'IFR_{acao}'].iloc[-1],0)} (sobrevendido)")
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
            print(
                f"Sobe após uma sequência de {dias_sequencia} dias de baixa: não aconteceu"
            )
        else:
            print(
                f"Sobe após uma sequência de {dias_sequencia} dias de baixa: {round(cont_sobe/(cont_continua_baixa + cont_sobe)*100,1)}% das vezes"
            )
        print(
            f"Estudo estatístico realizado nos últimos: {adj_close[f'close_{acao}'].count()} pregões"
        )
        print("-" * 60)


print("")
print("")
print(
    f"{len(acoes_s)} Ações em sequência de alta ou baixa maiores do que {dias} dias - {dt}:"
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
