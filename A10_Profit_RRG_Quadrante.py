import pandas as pd
import talib
import matplotlib.pyplot as plt
import os
import glob

def calcular_desempenho_relativo(ativo, indice):
    rs_ratio = (ativo / indice) * 100
    rs_ratio = ((rs_ratio - rs_ratio.ewm(span=21).mean()) / rs_ratio.ewm(span=21).std())*100
    return rs_ratio.round(2)

def calcular_momentum_relativo(ativo,indice):
    rs_momentum_a = talib.ROC(ativo, timeperiod=14)
    rs_momentum_i = talib.ROC(indice, timeperiod=14)
    rs_momentum = (rs_momentum_a / rs_momentum_i)*100
    rs_momentum = ((rs_momentum - rs_momentum.ewm(span=21).mean()) / rs_momentum.ewm(span=21).std())*100

    return rs_momentum.round(2)

def calcular_tendencia_cp(ativo):
    mme9 = talib.EMA(ativo, timeperiod=9)
    mme21 = talib.EMA(ativo, timeperiod=21)
    dif = mme9 - mme21
    return dif


def calcular_tendencia_lp(ativo):
    mme50 = talib.EMA(ativo, timeperiod=50)
    mme200 = talib.EMA(ativo, timeperiod=200)
    dif = mme50 - mme200
    return dif


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


# Diretório onde os arquivos .csv estão armazenados
data_dir = r"C:/Users/armen/OneDrive/Estratégias/Base/Diária"

list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*"
)  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)


# Lista de ativos
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

ativos = lista["Código"]

tendencia_CP = []
tendencia_LP = []
for codigo_acao in ativos:
    try:
        acao = pd.read_csv(
            f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{codigo_acao}_B_0_Diário.csv",
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
    except FileNotFoundError:
        print("Ação inválida. Tente novamente.")
        continue


    dados = pd.DataFrame()

    # Carrega a série histórica do IBOV
    ibov = pd.read_csv(
        "C:/Users/armen/OneDrive/Estratégias/Base/Diária/IBOV_B_0_Diário.csv",
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

    dados["Data"] = acao["Data"]
    dados["Ação"] = acao["Fechamento"]
    dados["Indice"] = ibov["Fechamento"]
    dados["Data"] = pd.to_datetime(dados["Data"], format="%d/%m/%Y")
    dados = dados.sort_values(by=["Data"], ascending=True)

    df = pd.DataFrame(dados)
    df = df.tail(1)

    # Calcular desempenho relativo e momentum relativo para cada ativo

    df[f"{acao}_tendencia_CP"] = calcular_momentum_relativo(dados["Ação"],dados["Indice"])
    df[f"{acao}_tendencia_LP"] = calcular_desempenho_relativo(dados["Ação"],dados["Indice"])

    tendencia_CP.append(df[f"{acao}_tendencia_CP"].iloc[-1])
    tendencia_LP.append(df[f"{acao}_tendencia_LP"].iloc[-1])





# Plotar o gráfico RRG
plt.figure(figsize=(8, 8))


# Adicionar a seta no final da linha de tendência
#    plt.arrow(df[f"{acao}_tendencia_CP"].iloc[-2], df[f"{acao}_tendencia_LP"].iloc[-2],
#              df[f"{acao}_tendencia_CP"].iloc[-1] - df[f"{acao}_tendencia_CP"].iloc[-2],
#              df[f"{acao}_tendencia_LP"].iloc[-1] - df[f"{acao}_tendencia_LP"].iloc[-2],
#              shape='full', color='red', lw=1, length_includes_head=True, head_width=10)


# Adicionar os pontos de dispersão
plt.scatter(tendencia_CP, tendencia_LP, label=f"ação")
# Adicionar nomes aos pontos usando annotate
for i, ativo in enumerate(ativos):
    plt.annotate(ativo, (tendencia_CP[i], tendencia_LP[i]), textcoords="offset points", xytext=(0, 5), ha='center')


# Color each quadrant
plt.fill_between([-400, 0], [-400, -400], [0, 0], color='red', alpha=0.2)
plt.fill_between([0, 400], [-400, -400], [0, 0], color='yellow', alpha=0.2)
plt.fill_between([400,0 ], [0, 0], [400, 400], color='green', alpha=0.2)
plt.fill_between([0, -400], [400, 400], [0, 0], color='blue', alpha=0.2)
# Add text labels in each corner
plt.text(-250, 250, 'Improving')
plt.text(250, 250, 'Leading')
plt.text(250, -250, 'Weakening')
plt.text(-250, -250, 'Lagging')





plt.axhline(0, color="black", linestyle="--", linewidth=0.8)
plt.axvline(0, color="black", linestyle="--", linewidth=0.8)
plt.title("Relative Rotation Graph")
plt.xlabel(f"Tendência CP")
plt.ylabel(f"Tendência LP")
plt.legend()
plt.grid(True)
plt.show()


