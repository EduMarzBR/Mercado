import numpy as np
import pandas as pd
import os
import glob
import plotly.graph_objs as go
import plotly.io as pio
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm
import warnings
from joblib import Parallel, delayed

#Este código usa os arquivos de séries históricas extraídos da plataforma Profit da Nelogica e os arquivos com a lista de ativos que compõem cada índice da B3 extraídos do site da B3.


# Ignora os warnings
warnings.simplefilter(action="ignore", category=FutureWarning)


# Nível de confiança para teste de estacionaridade
conf = 99

#realiza uma regressão linear nos últimos t registros de um DataFrame cot, e retorna os resíduos dessa regressão.
# Se não houver dados suficientes, ela retorna um DataFrame vazio.
def calculate_residual(cot, t):
    if cot.shape[0] < t:
        return pd.DataFrame()  # Retorna DataFrame vazio se não há dados suficientes
    X_independent = cot.iloc[-t:, 2].values.reshape(-1, 1)
    Y_dependent = cot.iloc[-t:, 1].values.reshape(-1, 1)
    reg = LinearRegression().fit(X_independent, Y_dependent)
    Y_predict = reg.predict(X_independent)
    residual = pd.DataFrame(np.array(Y_dependent - Y_predict), columns=["Residual"])
    return residual

#verifica se os resíduos de uma regressão linear nos últimos t registros de um DataFrame cot são estacionários,
# com um nível de confiança mínimo especificado por min_confidence. Se não houver dados suficientes para calcular
# os resíduos, a função retorna False.
def check_stationary(cot, t, min_confidence=conf):
    residual = calculate_residual(cot, t)
    if residual.empty:
        return False  # Retorna False se o residual estiver vazio
    residual_test = adfuller(residual["Residual"])
    confidence = 100 * (1 - residual_test[1])
    return confidence >= min_confidence

#calcula a estatística do teste de Dickey-Fuller aumentado para os resíduos de uma regressão linear nos últimos t
# registros de um DataFrame cot. Se não houver dados suficientes para calcular os resíduos, a função retorna np.nan.
# Caso contrário, ela retorna a estatística do teste ADF, que pode ser usada para avaliar a estacionaridade dos resíduos.
def adf_statistic(cot, t):
    residual = calculate_residual(cot, t)
    if residual.empty:
        return np.nan
    residual_test = adfuller(residual["Residual"])
    return residual_test[0]

# calcula a meia-vida de uma série temporal ts e os resultados da regressão autorregressiva,
# garantindo que não haja valores nulos ou infinitos durante o processo.
def half_life(ts):
    lagged = ts.shift(1).ffill().dropna()

    if lagged.isnull().values.any() or not np.isfinite(lagged).all():
        raise ValueError("Lagged series contains NaNs or infs")

    delta = ts - lagged
    delta = delta.dropna()

    if delta.isnull().values.any() or not np.isfinite(delta).all():
        raise ValueError("Delta contains NaNs or infs")

    X = sm.add_constant(lagged.values)

    if np.isnan(X).any() or not np.isfinite(X).all():
        raise ValueError("X contains NaNs or infs")

    ar_res = sm.OLS(delta, X).fit()
    half_life = (
        -1 * np.log(2) / ar_res.params.iloc[1]
    )  # Usando iloc para acessar o coeficiente
    return half_life, ar_res

#Imprime o par de long&short, o valor da meia-vida e o valor da estatística do teste de Dickey-Fuller aumentado.
def lista(x, y, cot, obs, texto, meiavida,l_est):
    print(x + " / " + y + " - " + obs + " - " + texto + " - " + str(meiavida))
    print(l_est)
    plot_pair(cot, x, y, meiavida)

#cria um gráfico interativo que visualiza a relação entre dois ativos, incluindo a média móvel e bandas de desvio padrão,
# e exibe essa visualização no navegador da web.
def plot_pair(cot, x, y, meiavida):
    df = cot.copy()

    trace_ratio = go.Scatter(
        x=df.index,
        y=df["Ratio"].iloc[252:],
        mode="lines",
        name=f"Ratio ({x}/{y})",
        line=dict(color="blue"),
    )

    trace_mean = go.Scatter(
        x=df.index,
        y=df["Média"].iloc[252:],
        mode="lines",
        name="Média Móvel",
        line=dict(color="orange"),
    )

    trace_upper_band = go.Scatter(
        x=df.index,
        y=df["Upper"].iloc[252:],
        mode="lines",
        name="3 Desvios Padrões Acima",
        line=dict(color="green"),
    )

    trace_lower_band = go.Scatter(
        x=df.index,
        y=df["Lower"].iloc[252:],
        mode="lines",
        name="3 Desvios Padrões Abaixo",
        line=dict(color="red"),
    )

    # Configurar o layout do gráfico
    layout = go.Layout(
        title=f"Ratio do Par {x}/{y} com Bandas de 3 Desvios Padrões - meia-vida {str(meiavida)}",
        xaxis=dict(title="Período"),
        yaxis=dict(title="Ratio"),
        legend=dict(x=0, y=1),
        hovermode="closest",
    )

    # Criar a figura
    fig = go.Figure(
        data=[trace_ratio, trace_mean, trace_upper_band, trace_lower_band],
        layout=layout,
    )
    # Adicionar uma pausa para permitir que o gráfico carregue corretamente
    pio.renderers.default = "browser"

    # Mostrar o gráfico
    pio.show(fig)


def process_pair(x, y):
    acn1 = pd.read_csv(
        f"C:/.../Base/Diária/{x}_B_0_Diário.csv",
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
        f"C:/.../Base/Diária/{y}_B_0_Diário.csv",
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

    cot["Ratio"] = cot[x] / cot[y]

    cot["Média"] = cot["Ratio"].rolling(252).mean()
    cot["STD"] = cot["Ratio"].rolling(252).std()
    cot["Upper"] = cot["Média"] + 3 * cot["STD"]
    cot["Lower"] = cot["Média"] - 3 * cot["STD"]

    hl, _ = half_life(cot["Ratio"].dropna())

    cot["Data"] = pd.to_datetime(cot["Data"], format="%Y-%m-%d")
    cot = cot.sort_values(by=["Data"], ascending=True)
    cot = cot.set_index(cot["Data"])
    tamanho_amostra = [120, 140, 160, 180, 200, 220, 240, 250]
    estacionaria = [check_stationary(cot, t, conf) for t in tamanho_amostra]

    tm = pd.DataFrame(tamanho_amostra, columns=["Tamanho da Amostra"])
    est = pd.DataFrame(estacionaria, columns=["Estacionária"])
    l_est = pd.concat([tm, est], axis=1)

    count_est= estacionaria.count(True)

    # Verifica se o Ratio atual está abaixo da banda inferior.  Se estiver abaixo e a meia-vida for menor que 20,
    # a função lista é chamada com os parâmetros relevantes para registrar e plotar os dados.
    # Se nenhuma condição for satisfeita, a função retorna None.

    if cot["Ratio"].iloc[-1] < cot["Lower"].iloc[-1]:
        if hl < 20:
            lista(
                x,
                y,
                cot,
                "Ficou abaixo do desvio padrão inferior",
                "meia-vida",
                round(hl, 0),
                l_est,
            )


    else:
        return None


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
print(indices)
print("")

# Solicita ao usuário que digite o número correspondente ao índice desejado
codigo = int(input("Digite o número do índice desejado: "))


# Verifica se o código digitado pelo usuário está no dicionário
if codigo in indices:
    indice = indices[codigo]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")

# Usando a biblioteca glob, o código gera uma lista de todos os arquivos no diretório especificado para o índice
# selecionado. O arquivo mais recente é então identificado usando os.path.getctime
# (que retorna a hora de criação do arquivo) e armazenado na variável latest_file.

list_of_files = glob.glob(f"C:/.../Listas/{indice}/*")
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

# Criação de uma lista contendo o código de todas as ações do índice selecionado
acoes = acoes_df["Setor"].tolist()

# Adiciona os ETFs BOVA11 e SMAL11 na lista de ações de modo que sejam criados pares com estes ativos.
acoes.append("BOVA11")
acoes.append("SMAL11")



# utiliza a biblioteca joblib para executar a função process_pair em todos os pares possíveis de ações na lista acoes
# de forma paralela, e depois imprime apenas os resultados que não são nulos.
# Isso permite um processamento mais rápido e eficiente dos pares de ações.

#Parallel(n_jobs=-1): Cria um objeto Parallel que executará tarefas em paralelo.
# O parâmetro n_jobs=-1 indica que todas as CPUs disponíveis devem ser usadas.

#delayed(process_pair)(x, y): A função process_pair é envolvida pela função delayed da biblioteca joblib.
# Isso permite que a função seja chamada de forma paralela.

#for i, x in enumerate(acoes) for y in acoes[i + 1 :]: Um loop duplo é usado para gerar todos os pares possíveis de
# ações na lista acoes. O loop externo itera sobre cada elemento x na lista acoes, e o loop interno itera sobre os
# elementos y que aparecem após x na lista, garantindo que cada par seja único (sem repetição e sem pares invertidos).

results = Parallel(n_jobs=-1)(
    delayed(process_pair)(x, y) for i, x in enumerate(acoes) for y in acoes[i + 1 :]
)

for result in results:
    if result is not None:
        print(result)
