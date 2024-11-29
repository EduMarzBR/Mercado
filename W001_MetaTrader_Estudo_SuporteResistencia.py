import MetaTrader5 as mt5
import pandas as pd
import glob
import os
from datetime import datetime
import talib as ta

mt5.initialize()




# Obtenção de dados históricos para o período especificado
periodo = 1000

ativo = "EMBR3"

percent_support_successful =[]
percent_support_false =[]
percent_resistance_successful =[]
percent_resistance_false = []


df = mt5.copy_rates_from(ativo, mt5.TIMEFRAME_D1, datetime.today(), periodo)
if df is not None and len(df) >= periodo:  # Verificação se df contém dados
    df = pd.DataFrame(df)
    df["time"] = pd.to_datetime(df["time"], unit="s")

    # Calcula médias móveis exponenciais de 9 e 21 períodos do fechamento
    df["EMA9"] = ta.EMA(df["close"], timeperiod=9)
    df["EMA21"] = ta.EMA(df["close"], timeperiod=21)

    #Calcula a média móvel exponencial de 21 períodos do volume
    df["EMAV21"] = ta.EMA(df["real_volume"], timeperiod=21)

    #Calcula ADX
    df["ADX"] = ta.ADX(df["close"], df["high"], df["low"], timeperiod=14)


    def identify_supports_resistances(df):
        supports = []
        resistances = []

        # Identificando suportes e resistências
        for i in range(3, len(df) - 3):
            # Verifica suporte
            if df["low"][i] < min(df["low"][i - 3 : i]) and df["low"][i] < min(
                df["low"][i + 1 : i + 4]):
                supports.append((df["time"][i], df["low"][i]))

            # Verifica resistência
            if df["high"][i] > max(df["high"][i - 3 : i]) and df["high"][i] > max(
                df["high"][i + 1 : i + 4]) :
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
                    row["time"] > time_s and row["low"] < support and row["EMA9"] < row["EMA21"]
                ):  # Rompimento de suporte
                    if (row["close"] < support ):
                        support_breakouts["successful"] += 1
                    else:
                        support_breakouts["false"] += 1
                    # Removendo o suporte da lista de não rompidos
                    supports.pop(-j - 1)
                    break

            # Análise de rompimento de resistência
            for j, (time_r, resistance) in enumerate(reversed(resistances)):
                if (
                    row["time"] > time_r and row["high"] > resistance and row["EMA9"] > row["EMA21"]
                ):  # Rompimento de resistência
                    if (row["close"] > resistance ):
                        resistance_breakouts["successful"] += 1
                    else:
                        resistance_breakouts["false"] += 1
                    # Removendo a resistência da lista de não rompidas
                    resistances.pop(-j - 1)
                    break

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


print(percentages)