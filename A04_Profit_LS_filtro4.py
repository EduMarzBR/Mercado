import numpy as np
import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm
import warnings
from joblib import Parallel, delayed

warnings.simplefilter(action="ignore", category=FutureWarning)

conf = 99
tamanho_amostra = [120, 140, 160, 180, 200, 220, 240, 260]


def calculate_residual(cot, t):
    if cot.shape[0] < t:
        return pd.DataFrame()  # Retorna DataFrame vazio se não há dados suficientes
    X_independent = cot.iloc[-t:, 2].values.reshape(-1, 1)
    Y_dependent = cot.iloc[-t:, 1].values.reshape(-1, 1)
    reg = LinearRegression().fit(X_independent, Y_dependent)
    Y_predict = reg.predict(X_independent)
    residual = pd.DataFrame(np.array(Y_dependent - Y_predict), columns=["Residual"])
    return residual


def check_stationary(cot, t, min_confidence=conf):
    residual = calculate_residual(cot, t)
    if residual.empty:
        return False  # Retorna False se o residual estiver vazio
    residual_test = adfuller(residual["Residual"])
    confidence = 100 * (1 - residual_test[1])
    return confidence >= min_confidence


def adf_statistic(cot, t):
    residual = calculate_residual(cot, t)
    if residual.empty:
        return np.nan
    residual_test = adfuller(residual["Residual"])
    return residual_test[0]


def half_life(ts):
    lagged = ts.shift(1).ffill()
    lagged = lagged.dropna()
    # Check for NaNs or infs in lagged
    if lagged.isnull().values.any() or not np.isfinite(lagged).all():
        raise ValueError("Lagged series contains NaNs or infs")

    delta = ts - lagged
    delta = delta.dropna()
    # Check for NaNs or infs in delta
    if delta.isnull().values.any() or not np.isfinite(delta).all():
        raise ValueError("Delta contains NaNs or infs")

    X = sm.add_constant(lagged.values)

    # Check for NaNs or infs in X
    if np.isnan(X).any() or not np.isfinite(X).all():
        raise ValueError("X contains NaNs or infs")

    ar_res = sm.OLS(delta, X).fit()
    half_life = -1 * np.log(2) / ar_res.params["x1"]
    return half_life, ar_res


def plot_residual(residual, t, x, y):
    df = residual.iloc[-t:].copy()
    std = residual["Z-Score"].std()
    up = 2 * std
    down = -2 * std
    stop_up = 3 * std
    stop_down = -3 * std

    plt.title(f"{x}/{y} Z-Score for t = {t}")
    residual["Z-Score"].plot(figsize=(14, 6))
    plt.axhline(y=0, color="y", linestyle="-")
    plt.axhline(y=up, color="b", linestyle="-")
    plt.axhline(y=down, color="b", linestyle="-")
    plt.axhline(y=stop_up, color="r", linestyle="-")
    plt.axhline(y=stop_down, color="r", linestyle="-")
    plt.show()


def tempo():
    temp = pd.read_csv(
        "C:/Users/armen/OneDrive/Estratégias/Base/Diária/PETR4_B_0_Diário.csv",
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
    tempo = pd.DataFrame(temp)
    tempo.set_index("Data")
    tempo.drop(
        columns=[
            "Ativo",
            "Fechamento",
            "Abertura",
            "Máximo",
            "Mínimo",
            "Volume",
            "Quantidade",
        ],
        inplace=True,
    )
    tempo["Data"] = pd.to_datetime(tempo["Data"], format="%d/%m/%Y")
    tempo = tempo.sort_values(by=["Data"], ascending=True)
    return tempo["Data"][-490:]


def process_pair(x, y, tamanho_amostra, conf):
    acn1 = pd.read_csv(
        f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{x}_B_0_Diário.csv",
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
    acn2 = pd.read_csv(
        f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{y}_B_0_Diário.csv",
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

    df1 = acn1[["Data", "Fechamento"]].rename(columns={"Fechamento": x})
    df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")
    df1 = df1.sort_values(by=["Data"], ascending=True)
    df2 = acn2[["Data", "Fechamento"]].rename(columns={"Fechamento": y})
    df2["Data"] = pd.to_datetime(df2["Data"], format="%d/%m/%Y")
    df2 = df2.sort_values(by=["Data"], ascending=True)

    cot = pd.merge(df1, df2, how="inner", on="Data")
    cot.dropna(inplace=True)

    if len(cot) < max(tamanho_amostra):
        return None, None, None

    estacionaria = [check_stationary(cot, t, conf) for t in tamanho_amostra]

    if estacionaria.count(True) >= 7:
        residual = calculate_residual(cot, max(tamanho_amostra))
        if residual.empty:
            return None, None, None
        mean = float(residual.mean().iloc[0])
        std = float(residual.std().iloc[0])
        k = 3
        up = float(mean + std * k)
        down = float(mean - std * k)
        residual["Z-Score"] = (
            residual["Residual"] - residual["Residual"].mean()
        ) / residual["Residual"].std()
        hl, _ = half_life(residual["Residual"])

        if hl <= 10 and hl > 0:
            if (
                up < residual["Residual"].iloc[-1]
                or down > residual["Residual"].iloc[-1]
            ):
                plot_residual(residual, max(tamanho_amostra), x, y)
                return f"{x}/{y}", hl, residual["Residual"].iloc[-1]
    return None, None, None


def main():
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
        return

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
    )

    nova_lista = []
    cot = tempo()
    for x in lista["Setor"]:
        acn = pd.read_csv(
            f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{x}_B_0_Diário.csv",
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
        acn["Data"] = pd.to_datetime(acn["Data"], format="%d/%m/%Y")
        acn = acn.sort_values(by=["Data"], ascending=True)
        acn = acn.loc[acn["Data"].isin(cot)]
        if len(acn) >= 250:
            nova_lista.append(x)

    results = Parallel(n_jobs=-1)(
        delayed(process_pair)(x, y, tamanho_amostra, conf)
        for i, x in enumerate(nova_lista)
        for y in nova_lista[i + 1 :]
    )

    for result in results:
        if result[0] is not None:
            print(result)


if __name__ == "__main__":
    main()
