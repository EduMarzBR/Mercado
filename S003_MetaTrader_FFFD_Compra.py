import pandas as pd
import glob
import os
from datetime import datetime
import talib
import warnings
import MetaTrader5 as mt5

warnings.filterwarnings("ignore")
k = 1000
periodo = 1000
mt5.initialize()
def identificar_FFFD(df):
    bb = talib.BBANDS(df["close"], timeperiod=20, nbdevup=2, nbdevdn=2)
    m = bb[1]
    bi = bb[2]
    close = df["close"]
    signals = pd.Series(index=df.index)
    signals[:] = 0

    for i in range(20, len(close)):
        if close.iloc[i - 2] < bi.iloc[i - 2]:
            if close.iloc[i - 1] > bi.iloc[i - 1] and close.iloc[i - 1] < m.iloc[i - 1]:
                signals.iloc[i - 1] = 1

    return signals


def preco_entrada(df):
    p_entrada = pd.Series(index=df.index)
    p_entrada[:] = 0
    for i in range(20, len(df)):
        if df["FFFD"].iloc[i - 1] == 1:
            p_entrada.iloc[i] = df["high"].iloc[i - 1] + 0.01
        elif (
            df["FFFD"].iloc[i - 2] == 1
            and df["high"].iloc[i - 2] > df["high"].iloc[i - 1]
            and df["low"].iloc[i - 2] < df["low"].iloc[i - 1]
        ):
            p_entrada.iloc[i] = df["high"].iloc[i - 2] + 0.01

    return p_entrada


def preco_objetivo(df):
    bb = talib.BBANDS(df["close"], timeperiod=20, nbdevup=2, nbdevdn=2)
    m = bb[1]
    p_objetivo = pd.Series(index=df.index)
    p_objetivo[:] = 0
    for i in range(20, len(df)):
        if df["FFFD"].iloc[i - 1] == 1:
            p_objetivo.iloc[i] = m.iloc[i]
        elif (
            df["FFFD"].iloc[i - 2] == 1
            and df["high"].iloc[i - 2] > df["high"].iloc[i - 1]
            and df["low"].iloc[i - 2] < df["low"].iloc[i - 1]
        ):
            p_objetivo.iloc[i] = m.iloc[i]

    return p_objetivo


def preco_stop_loss(df):
    p_stop_loss = pd.Series(index=df.index)
    p_stop_loss[:] = 0
    for i in range(20, len(df)):
        if df["FFFD"].iloc[i - 1] == 1:
            p_stop_loss.iloc[i] = df["low"].iloc[i - 1] - 0.01
        elif (
            df["FFFD"].iloc[i - 2] == 1
            and df["high"].iloc[i - 2] > df["high"].iloc[i - 1]
            and df["low"].iloc[i - 2] < df["low"].iloc[i - 1]
        ):
            p_stop_loss.iloc[i] = df["low"].iloc[i - 2] - 0.01
    return p_stop_loss


def lista_operacoes(df):
    entrada = pd.Series(index=df.index)
    entrada[:] = 0
    objetivo = pd.Series(index=df.index)
    objetivo[:] = 0
    stop_loss = pd.Series(index=df.index)
    stop_loss[:] = 0
    dt_fim = pd.Series(index=df.index)
    dt_fim[:] = 3
    resultado = pd.Series(index=df.index)
    resultado[:] = 3
    p_saida = pd.Series(index=df.index)
    p_saida[:] = 3
    resultado_final = pd.Series(index=df.index)
    resultado_final[:] = 3
    trades_perct = pd.Series(index=df.index)
    trades_perct[:] = 3
    m = talib.BBANDS(df["close"], timeperiod=20, nbdevup=2, nbdevdn=2)[1]
    real_volume = df["real_volume"]
    real_volume_mean = df["real_volume"].rolling(10).mean()
    for i in range(20, len(df)):
        if (
            df["FFFD"].iloc[i - 1] == 1
            and df["high"].iloc[i] >= df["high"].iloc[i - 1] + 0.01
            #and real_volume.iloc[i] > real_volume_mean.iloc[i]
        ):
            if (
                df["low"].iloc[i] <= df["high"].iloc[i - 1] + 0.01
                and df["open"].iloc[i] > df["low"].iloc[i - 1]
            ):
                # Filtra operações que tenham potencial de ganho maior do que potencial de perda
                if (
                    df["Preço Objetivo"].iloc[i] is not None
                    and df["Preço Stop"].iloc[i] is not None
                ):
                    if (
                        (df["Preço Objetivo"].iloc[i] - df["Preço Entrada"].iloc[i])
                        / df["Preço Entrada"].iloc[i]
                    ) > abs(
                        (df["Preço Stop"].iloc[i] - df["Preço Entrada"].iloc[i])
                        / df["Preço Entrada"].iloc[i]
                    ):
                        entrada.iloc[i] = df["high"].iloc[i - 1] + 0.01
                        objetivo.iloc[i] = m.iloc[i]
                        stop_loss.iloc[i] = df["low"].iloc[i - 1] - 0.01
        elif (
            df["FFFD"].iloc[i - 2] == 1
            and df["high"].iloc[i - 2] > df["high"].iloc[i - 1]
            and df["low"].iloc[i - 2] < df["low"].iloc[i - 1]
            and df["high"].iloc[i] >= df["high"].iloc[i - 2] + 0.01
            #and real_volume.iloc[i] > real_volume_mean.iloc[i]
        ):
            if (
                df["low"].iloc[i] <= df["high"].iloc[i - 2] + 0.01
                and df["open"].iloc[i] > df["low"].iloc[i - 2]
            ):
                if (
                    df["Preço Objetivo"].iloc[i] is not None
                    and df["Preço Stop"].iloc[i] is not None
                ):
                    if (
                        (df["Preço Objetivo"].iloc[i] - df["Preço Entrada"].iloc[i])
                        / df["Preço Entrada"].iloc[i]
                    ) > abs(
                        (df["Preço Stop"].iloc[i] - df["Preço Entrada"].iloc[i])
                        / df["Preço Entrada"].iloc[i]
                    ):
                        entrada.iloc[i] = df["high"].iloc[i - 1] + 0.01
                        objetivo.iloc[i] = m.iloc[i]
                        stop_loss.iloc[i] = df["low"].iloc[i - 1] - 0.01

    operacoes = pd.concat(
        [
            entrada,
            objetivo,
            stop_loss,
            dt_fim,
            resultado,
            p_saida,
            resultado_final,
            trades_perct,
        ],
        axis=1,
    )
    operacoes.columns = [
        "Preço Entrada",
        "Preço Objetivo",
        "Preço Stop",
        "Data Fim",
        "Resultado",
        "Preço Saida",
        "Resultado Final",
        "Trades (%)",
    ]

    return operacoes


def calcular_operacoes(df, operacoes, k):
    # Faz um loop para percorrer as operações e em seguida percorre cada dia, da data de início da operação para frente
    # verificando se a ação alcança o objetivo ou o stop loss. Se alcançar o objetivo e o stop loss no mesmo dia, esta operação
    # não será contabilizada.
    for o in range(0, len(operacoes)):
        for i in range(20, len(df)):
            if df.index[i] >= operacoes.index[o]:
                if (
                    operacoes["Preço Objetivo"].iloc[o] < df["high"].iloc[i]
                    and operacoes["Preço Stop"].iloc[o] < df["low"].iloc[i]
                ):
                    operacoes["Data Fim"].iloc[o] = df.index[i]
                    operacoes["Resultado"].iloc[o] = 1
                    if operacoes["Preço Objetivo"].iloc[o] < df["open"].iloc[i]:
                        operacoes["Preço Saida"].iloc[o] = df["open"].iloc[i]
                        operacoes["Trades (%)"].iloc[o] = round(
                            (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                / operacoes["Preço Entrada"].iloc[o]
                            )
                            * 100,
                            2,
                        )

                        # se for a primeira operação o valor inicial será igual k
                        if o == 0:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (k / operacoes["Preço Entrada"].iloc[o])
                            ) + k
                            break
                        else:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (
                                    operacoes["Resultado Final"].iloc[o - 1]
                                    / operacoes["Preço Entrada"].iloc[o]
                                )
                            ) + operacoes["Resultado Final"].iloc[o - 1]
                            break

                    else:
                        operacoes["Preço Saida"].iloc[o] = operacoes[
                            "Preço Objetivo"
                        ].iloc[o]
                        operacoes["Trades (%)"].iloc[o] = round(
                            (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                / operacoes["Preço Entrada"].iloc[o]
                            )
                            * 100,
                            2,
                        )

                        # se for a primeira operação o valor inicial será igual k
                        if o == 0:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (k / operacoes["Preço Entrada"].iloc[o])
                            ) + k
                            break
                        else:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (
                                    operacoes["Resultado Final"].iloc[o - 1]
                                    / operacoes["Preço Entrada"].iloc[o]
                                )
                            ) + operacoes["Resultado Final"].iloc[o - 1]
                            break
                elif (
                    operacoes["Preço Objetivo"].iloc[o] > df["high"].iloc[i]
                    and operacoes["Preço Stop"].iloc[o] > df["low"].iloc[i]
                ):
                    operacoes["Data Fim"].iloc[o] = df.index[i]
                    operacoes["Resultado"].iloc[o] = -1
                    if operacoes["Preço Stop"].iloc[o] > df["open"].iloc[i]:
                        operacoes["Preço Saida"].iloc[o] = df["open"].iloc[i]
                        operacoes["Trades (%)"].iloc[o] = round(
                            (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                / operacoes["Preço Entrada"].iloc[o]
                            )
                            * 100,
                            2,
                        )

                        # se for a primeira operação o valor inicial será igual k
                        if o == 0:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (k / operacoes["Preço Entrada"].iloc[o])
                            ) + k
                            break
                        else:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (
                                    operacoes["Resultado Final"].iloc[o - 1]
                                    / operacoes["Preço Entrada"].iloc[o]
                                )
                            ) + operacoes["Resultado Final"].iloc[o - 1]
                            break
                    else:
                        operacoes["Data Fim"].iloc[o] = df.index[i]
                        operacoes["Preço Saida"].iloc[o] = (
                            operacoes["Preço Stop"].iloc[o] - 0.01
                        )
                        operacoes["Trades (%)"].iloc[o] = round(
                            (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                / operacoes["Preço Entrada"].iloc[o]
                            )
                            * 100,
                            2,
                        )

                        # se for a primeira operação o valor inicial será igual k
                        if o == 0:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (k / operacoes["Preço Entrada"].iloc[o])
                            ) + k
                            break
                        else:
                            operacoes["Resultado Final"].iloc[o] = (
                                (
                                    operacoes["Preço Saida"].iloc[o]
                                    - operacoes["Preço Entrada"].iloc[o]
                                )
                                * (
                                    operacoes["Resultado Final"].iloc[o - 1]
                                    / operacoes["Preço Entrada"].iloc[o]
                                )
                            ) + operacoes["Resultado Final"].iloc[o - 1]
                            break

                elif (
                    operacoes["Preço Objetivo"].iloc[o] < df["high"].iloc[i]
                    and operacoes["Preço Stop"].iloc[o] > df["low"].iloc[i]
                ):
                    operacoes["Data Fim"].iloc[o] = df.index[i]
                    operacoes["Resultado"].iloc[o] = "e"
                    operacoes["Preço Saida"].iloc[o] = "e"
                    operacoes["Trades (%)"].iloc[o] = "e"
                    operacoes["Resultado Final"].iloc[o] = operacoes[
                        "Resultado Final"
                    ].iloc[o - 1]
                    break

                else:
                    operacoes["Resultado"].iloc[o] = 0
                    operacoes["Resultado Final"].iloc[o] = operacoes[
                        "Resultado Final"
                    ].iloc[o - 1]

    return operacoes


# Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")


def screening_FFFD(df):
    bb = talib.BBANDS(df["close"], timeperiod=20, nbdevup=2, nbdevdn=2)
    m = bb[1]
    bi = bb[2]
    real_volume = df["real_volume"]
    real_volume_mean = df["real_volume"].rolling(10).mean()
    signals = 0

    close = df["close"]

    for i in range(20, len(close)):
        if close.iloc[-2] < bi.iloc[-2]:
            if close.iloc[-1] > bi.iloc[-1] and close.iloc[-1] < m.iloc[-1]:
                if real_volume.iloc[-1] > real_volume_mean.iloc[-1]:
                    signals = 1
        elif close.iloc[-3] < bi.iloc[-3]:
            if close.iloc[-2] > bi.iloc[-2] and close.iloc[-2] < m.iloc[-2]:
                if real_volume.iloc[-2] > real_volume_mean.iloc[-2]:
                     signals = 2
    return signals


def screening_preco_entrada(signals, df):
    p_entrada = 0
    if signals == 1:
        p_entrada = df["high"].iloc[-1] + 0.01
    elif signals == 2:
        p_entrada = df["high"].iloc[-2] + 0.01

    return p_entrada


def screening_preco_objetivo(signals, df):
    bb = talib.BBANDS(df["close"], timeperiod=20, nbdevup=2, nbdevdn=2)
    bs = bb[0]
    bi= bb[2]
    p_objetivo = 0
    if signals == 1:
        p_objetivo = bs.iloc[-1]
    elif signals == 2:
        p_objetivo = bi.iloc[-1]

    return p_objetivo


def screening_preco_stop_loss(signals, df):
    p_stop_loss = 0
    if signals == 1:
        p_stop_loss = df["low"].iloc[-1] - 0.01
    elif signals == 2:
        p_stop_loss = df["low"].iloc[-2] - 0.01

    return p_stop_loss



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
analise = []

screening = []

for acao in acoes:
    # Carregar o arquivo CSV usando pandas
    df = mt5.copy_rates_from(acao, mt5.TIMEFRAME_D1, datetime.today(), periodo)
    df = pd.DataFrame(df)
    if df.empty:
        continue
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)

    df["FFFD"] = identificar_FFFD(df)

    df["Preço Entrada"] = preco_entrada(df)

    df["Preço Objetivo"] = preco_objetivo(df)

    df["Preço Stop"] = preco_stop_loss(df)

    # Cria a lista de operações que satisfazem as condições de entrada
    operaoes = lista_operacoes(df)

    operacoes = operaoes[(operaoes != 0).all(axis=1)]

    calc_oper = calcular_operacoes(df, operacoes, k)
    calc_oper.replace("e", 0, inplace=True)
    # exclui as operações que ainda não foram encerradas
    condition1 = calc_oper["Data Fim"] == 3
    condition2 = calc_oper["Resultado Final"] == 3
    calc_oper = calc_oper[~condition1]
    calc_oper = calc_oper[~condition2]
    if calc_oper.empty:
        continue
    resultado_final = calc_oper["Resultado Final"].iloc[-1]
    payoff = round(resultado_final - k, 2)
    numero_operacoes = calc_oper.shape[0]
    media_operacoes = round(resultado_final / numero_operacoes, 2)
    operacoes_gain = calc_oper[calc_oper["Resultado"] > 0].shape[0]
    operacoes_loss = calc_oper[calc_oper["Resultado"] < 0].shape[0]
    ativo = acao
    if numero_operacoes > 0:
        percent_gain = round((operacoes_gain / numero_operacoes) * 100, 2)
    else:
        percent_gain = 0
    if numero_operacoes > 0:
        percent_loss = round((operacoes_loss / numero_operacoes) * 100, 2)
    else:
        percent_loss = 0
    if percent_gain > percent_loss:
        desempenho = "Gain"
    elif percent_loss == percent_gain:
        desempenho = "Equal"
    else:
        desempenho = "Loss"

    dados = {
        "Ativo": ativo,
        "Resultado Final": resultado_final,
        "Número Operações": numero_operacoes,
        "Payoff": payoff,
        "Payoff (%)": round(payoff / k * 100, 2),
        "Operações Gain": operacoes_gain,
        "Operações Loss": operacoes_loss,
        "Percentual Gain": percent_gain,
        "Percentual Loss": percent_loss,
        "Desempenho": desempenho,
    }
    df_resultado = pd.DataFrame(dados, index=[0])
    analise.append(
        df_resultado[
            [
                "Ativo",
                "Resultado Final",
                "Número Operações",
                "Payoff",
                "Payoff (%)",
                "Operações Gain",
                "Operações Loss",
                "Percentual Gain",
                "Percentual Loss",
                "Desempenho",
            ]
        ]
    )
    sinal = screening_FFFD(df)
    if sinal == 1:
        p_entrada = screening_preco_entrada(sinal, df)
        p_objetivo = screening_preco_objetivo(sinal, df)
        p_stop = screening_preco_stop_loss(sinal, df)
        scrn = {
            "Ativo": ativo,
            "Sinal": sinal,
            "Preço Entrada": p_entrada,
            "Preço Objetivo": p_objetivo,
            "Preço Stop": p_stop,
        }
        df_screening = pd.DataFrame(scrn, index=[0])
        screening.append(
            df_screening[
                ["Ativo", "Sinal", "Preço Entrada", "Preço Objetivo", "Preço Stop"]
            ]
        )


if len(analise) > 0:
    merged_analise = pd.concat(analise)
    merged_analise.to_excel("analise_FFFD_compra.xlsx", index=False)
    print("Estudo salvo em analise_FFFD_compra.xlsx")


if len(screening) > 0:
    merged_scrn = pd.concat(screening)
    ativos_scrn = merged_scrn["Ativo"]

    print("")
    print("'")
    print("-" * 60)

    for ativo_scrn in ativos_scrn:
        merged_scrn_select = merged_scrn[merged_scrn["Ativo"] == ativo_scrn]
        scrn_ativo = merged_scrn_select["Ativo"].iloc[0]
        scrn_p_entrada = merged_scrn_select["Preço Entrada"].iloc[0]
        scrn_p_objetivo = merged_scrn_select["Preço Objetivo"].iloc[0]
        scrn_per_ganho = round(
            (
                (
                    merged_scrn_select["Preço Objetivo"].iloc[0]
                    - merged_scrn_select["Preço Entrada"].iloc[0]
                )
                / merged_scrn_select["Preço Entrada"].iloc[0]
            )
            * 100,
            2,
        )
        scrn_p_stop = merged_scrn_select["Preço Stop"].iloc[0]
        scrn_per_perda = round(
            (
                (
                    merged_scrn_select["Preço Stop"].iloc[0]
                    - merged_scrn_select["Preço Entrada"].iloc[0]
                )
                / merged_scrn_select["Preço Entrada"].iloc[0]
            )
            * 100,
            2,
        )

        merged_analise_scrn = merged_analise[merged_analise["Ativo"] == ativo_scrn]
        scrn_per_gain = merged_analise_scrn["Percentual Gain"].iloc[0]
        scrn_per_loss = merged_analise_scrn["Percentual Loss"].iloc[0]
        scrn_payoff_percent = merged_analise_scrn["Payoff (%)"].iloc[0]

        if scrn_per_gain >= 50: # and scrn_payoff_percent > 40:

            scrn_resultado = merged_analise_scrn["Resultado Final"].iloc[0]
            scrn_numero_oper = merged_analise_scrn["Número Operações"].iloc[0]
            if scrn_per_gain > abs(scrn_per_loss):
                print("")
                print(f"Ação: ${scrn_ativo}")
                print(f"Preço de entrada: {round(scrn_p_entrada, 2)}")
                print(f"Objetivo: {round(scrn_p_objetivo,2)}")
                print(f"Percentual de ganho: {round(scrn_per_ganho,2)}%")
                print(f"Preço de stop: {round(scrn_p_stop,2)}")
                print(f"Percentual de perda: {round(scrn_per_perda,2)}%")
                print("Estatísticas:")
                print(f"Estudo estatístico realizado nos últimos: {len(df)} pregões")
                print(f"Número de operações realizadas: {scrn_numero_oper}")
                print(f"Payoff (%): {round(scrn_payoff_percent,2)}%")
                print(f"Percentual de operações com ganho: {round(scrn_per_gain,2)}%")
                print(f"Percentual de operações com perda: {round(scrn_per_loss,2)}%")
                print("-" * 60)

print(f"")
print(f"")

print(
    f"Estratégia Fechou Fora Fechou Dentro (FFFD) de Compra com histórico de acerto maior ou igual a 50%. - {dt}  "

)
print(f"")
print(
    f"-Caso o preço de abertura seja menor do que o preço de stop, ou o preço alcance o preço de stop antes do preço de"
    f" entrada, a operação deverá ser cancelada."
)
print(
    f"-Caso o preço de abertura seja maior do que o preço de entrada, aguarde até que o preço seja igual ao preço de "
    f"entrada."
)