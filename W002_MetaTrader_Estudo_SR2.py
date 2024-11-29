import MetaTrader5 as mt5
import pandas as pd
import glob
import os
from datetime import datetime
import talib as ta

mt5.initialize()

# Configuração de variáveis
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

# Solicitação de índice ao usuário
codigo = int(input("Digite o número do índice desejado: "))

# Verificação do código do índice
if codigo in indices:
    indice = indices[codigo]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")

# Obtenção do arquivo mais recente para o índice selecionado
list_of_files = glob.glob(f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*")
latest_file = max(list_of_files, key=os.path.getctime)

# Leitura do arquivo CSV que contém a lista de ações do índice selecionado
acoes_df = pd.read_csv(
    latest_file,
    sep=";",
    encoding="ISO-8859-1",
    skiprows=0,
    skipfooter=2,
    engine="python",
    thousands=".",
    decimal=",",
    header=1,
)
acoes = acoes_df["Setor"].tolist()


# Obtenção de dados históricos para o período especificado
periodo = 1000
retornos = pd.DataFrame()


percent_support_successful = []
percent_support_false = []
percent_resistance_successful = []
percent_resistance_false = []

for ativo in acoes:
    df = mt5.copy_rates_from(ativo, mt5.TIMEFRAME_D1, datetime.today(), periodo)
    if df is not None and len(df) >= periodo:  # Verificação se df contém dados
        df = pd.DataFrame(df)
        df["time"] = pd.to_datetime(df["time"], unit="s")

        # Calcula médias móveis exponenciais de 9 e 21 períodos do fechamento
        df["EMA9"] = ta.EMA(df["close"], timeperiod=9)
        df["EMA21"] = ta.EMA(df["close"], timeperiod=21)

        # Calcula a média móvel exponencial de 21 períodos do volume
        df["EMAV21"] = ta.EMA(df["real_volume"], timeperiod=21)

        # Calcula ADX
        df["ADX"] = ta.ADX(df["close"], df["high"], df["low"], timeperiod=14)

        # Calcula MACD
        df["MACD"], df["MACD_signal"], df["MACD_hist"] = ta.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)

        def identify_supports_resistances(df):
            supports = []
            resistances = []

            # Identificando suportes e resistências
            for i in range(3, len(df) - 3):
                # Verifica suporte
                if df["low"][i] < min(df["low"][i - 3 : i]) and df["low"][i] < min(
                    df["low"][i + 1 : i + 4]
                ):
                    supports.append((df["time"][i], df["low"][i]))

                # Verifica resistência
                if df["high"][i] > max(df["high"][i - 3 : i]) and df["high"][i] > max(
                    df["high"][i + 1 : i + 4]
                ):
                    resistances.append((df["time"][i], df["high"][i]))

            return supports, resistances

        def analyze_breakouts(df, supports, resistances):
            support_breakouts = {"successful": 0, "false": 0}
            resistance_breakouts = {"successful": 0, "false": 0}

            # Loop pelo DataFrame para detectar rompimentos
            for i, row in df.iterrows():
                # Análise de rompimento de suporte
                for j, (time_s, support) in enumerate(reversed(supports)):
                    if (
                        row["time"] > time_s and row["low"] < support and row["MACD"] < row["MACD_signal"] and row["ADX"] > 25 and row["ADX"] < 50
                    ):  # Rompimento de suporte
                        if row["close"] < support:
                            support_breakouts["successful"] += 1
                            # Removendo o suporte da lista de não rompidos
                            supports.pop(-j - 1)
                            break
                        else:
                            support_breakouts["false"] += 1

                # Análise de rompimento de resistência
                for j, (time_r, resistance) in enumerate(reversed(resistances)):
                    if (
                        row["time"] > time_r and row["high"] > resistance and row["MACD"] > row["MACD_signal"] and row["ADX"] > 25 and row["ADX"] < 50
                    ):  # Rompimento de resistência
                        if row["close"] > resistance:
                            resistance_breakouts["successful"] += 1
                            # Removendo a resistência da lista de não rompidas
                            resistances.pop(-j - 1)
                            break
                        else:
                            resistance_breakouts["false"] += 1

            return support_breakouts, resistance_breakouts

        def calculate_percentages(support_breakouts, resistance_breakouts):
            total_support_breakouts = (
                support_breakouts["successful"] + support_breakouts["false"]
            )
            total_resistance_breakouts = (
                resistance_breakouts["successful"] + resistance_breakouts["false"]
            )

            percent_support_successful = (
                (support_breakouts["successful"] / total_support_breakouts) * 100
                if total_support_breakouts > 0
                else 0
            )
            percent_support_false = (
                (support_breakouts["false"] / total_support_breakouts) * 100
                if total_support_breakouts > 0
                else 0
            )

            percent_resistance_successful = (
                (resistance_breakouts["successful"] / total_resistance_breakouts) * 100
                if total_resistance_breakouts > 0
                else 0
            )
            percent_resistance_false = (
                (resistance_breakouts["false"] / total_resistance_breakouts) * 100
                if total_resistance_breakouts > 0
                else 0
            )

            return {
                "percent_support_successful": percent_support_successful,
                "percent_support_false": percent_support_false,
                "percent_resistance_successful": percent_resistance_successful,
                "percent_resistance_false": percent_resistance_false,
            }

        # Aplicando as funções no DataFrame df
        supports, resistances = identify_supports_resistances(df)
        support_breakouts, resistance_breakouts = analyze_breakouts(
            df, supports, resistances
        )
        percentages = calculate_percentages(support_breakouts, resistance_breakouts)

        percent_support_successful.append(
            [f"-${ativo}-", percentages["percent_support_successful"]]
        )
        percent_support_false.append(
            [f"-${ativo}-", percentages["percent_support_false"]]
        )
        percent_resistance_successful.append(
            [f"-${ativo}-", percentages["percent_resistance_successful"]]
        )
        percent_resistance_false.append(
            [f"-${ativo}-", percentages["percent_resistance_false"]]
        )

obs_ativos = len(percent_support_successful)

print("Ativos observados", obs_ativos)
print("")
percent_support_successful = pd.DataFrame(percent_support_successful)
percent_support_successful.rename(
    columns={0: "ativo", 1: "percent_support_successful"}, inplace=True
)
percent_support_false = pd.DataFrame(percent_support_false)
percent_support_false.rename(
    columns={0: "ativo", 1: "percent_support_false"}, inplace=True
)
percent_resistance_successful = pd.DataFrame(percent_resistance_successful)
percent_resistance_successful.rename(
    columns={0: "ativo", 1: "percent_resistance_successful"}, inplace=True
)
percent_resistance_false = pd.DataFrame(percent_resistance_false)
percent_resistance_false.rename(
    columns={0: "ativo", 1: "percent_resistance_false"}, inplace=True
)


percent_support_successful_mean = sum(
    percent_support_successful["percent_support_successful"]
) / len(percent_support_successful)
percent_support_false_mean = sum(percent_support_false["percent_support_false"]) / len(
    percent_support_false
)
print("percent_support_successful_mean", round(percent_support_successful_mean, 2))
print("percent_support_false_mean", round(percent_support_false_mean, 2))

percent_resistance_successful_mean = sum(
    percent_resistance_successful["percent_resistance_successful"]
) / len(percent_resistance_successful)
percent_resistance_false_mean = sum(
    percent_resistance_false["percent_resistance_false"]
) / len(percent_resistance_false)
print(
    "percent_resistance_successful_mean", round(percent_resistance_successful_mean, 2)
)
print("percent_resistance_false_mean", round(percent_resistance_false_mean, 2))

print("")
percent_support_successful_5mais = percent_support_successful.nlargest(
    5, "percent_support_successful"
)
print("percent_support_successful_5mais", percent_support_successful_5mais)

percent_support_false_5mais = percent_support_false.nlargest(5, "percent_support_false")
print("percent_support_false_5mais", percent_support_false_5mais)

percent_resistance_successful_5mais = percent_resistance_successful.nlargest(
    5, "percent_resistance_successful"
)
print("percent_resistance_successful_5mais", percent_resistance_successful_5mais)

percent_resistance_false_5mais = percent_resistance_false.nlargest(
    5, "percent_resistance_false"
)
print("percent_resistance_false_5mais", percent_resistance_false_5mais)


"""
percent_support_successful_mean = sum(percent_support_successful)/len(percent_support_successful)
percent_support_false_mean = sum(percent_support_false)/len(percent_support_false)
percent_resistance_successful_mean = sum(percent_resistance_successful)/len(percent_resistance_successful)
percent_resistance_false_mean = sum(percent_resistance_false)/len(percent_resistance_false)

print("percent_support_successful_mean", percent_support_successful_mean)
print("percent_support_false_mean", percent_support_false_mean)
print("percent_resistance_successful_mean", percent_resistance_successful_mean)
print("percent_resistance_false_mean", percent_resistance_false_mean)
"""
