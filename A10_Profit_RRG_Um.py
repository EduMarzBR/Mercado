import pandas as pd
import talib
import matplotlib.pyplot as plt


def calcular_desempenho_relativo(ativo, indice, period=14):
    rs_ratio = (ativo.pct_change() / indice.pct_change()) * 100
    rs_ratio = rs_ratio.ewm(span=period).mean()
    # Defina os limites desejados
    new_min = 96
    new_max = 104

    # Calcule o Min-Max Scaling para os novos limites
    rs_ratio = ((rs_ratio - rs_ratio.min()) / (rs_ratio.max() - rs_ratio.min())) * (
        new_max - new_min
    ) + new_min

    # rs_ratio = rs_ratio.diff()
    return rs_ratio.round(2)


def calcular_momentum_relativo(ativo, indice, period=14, period2=14):
    # Verificar se as listas têm o mesmo comprimento
    if len(ativo) != len(indice):
        raise ValueError("As listas 'ativo' e 'indice' devem ter o mesmo comprimento.")

    rs_ratio = (ativo.pct_change() / indice.pct_change()) * 100
    rs_ratio = rs_ratio.ewm(span=period).mean()
    # Defina os limites desejados
    new_min = 96
    new_max = 104

    # Calcule o Min-Max Scaling para os novos limites
    rs_ratio = ((rs_ratio - rs_ratio.min()) / (rs_ratio.max() - rs_ratio.min())) * (
        new_max - new_min
    ) + new_min

    # Calcular o ROC
    rs_momentum = talib.ROC(rs_ratio, timeperiod=period)


    #rs_momentum = rs_momentum.ewm(span=period2, adjust=False).mean()
    new_min = 96
    new_max = 104

    # Calcule o Min-Max Scaling para os novos limites
    rs_momentum = (
        (rs_momentum - rs_momentum.min()) / (rs_momentum.max() - rs_momentum.min())
    ) * (new_max - new_min) + new_min

    return rs_momentum.round(2)


codigo_acao = True
while codigo_acao is True:
    # Solicita ao usuário que digite o código da ação
    codigo_acao = input("Digite o código da ação: ").upper()

    # Mensagem de boas-vindas e exibe o código inserido
    print(f"Bem-vindo! Você digitou o código da ação: {codigo_acao}")

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
df = df.tail(5)

# Calcular desempenho relativo e momentum relativo para cada ativo

df[f"{codigo_acao}_tendencia_CP"] = calcular_momentum_relativo(
    dados["Ação"], dados["Indice"]
)
df[f"{codigo_acao}_tendencia_LP"] = calcular_desempenho_relativo(
    dados["Ação"], dados["Indice"]
)

# Plotar o gráfico RRG
plt.figure(figsize=(8, 8))

# Adicionar a linha conectando os pontos
plt.plot(
    df[f"{codigo_acao}_tendencia_LP"],
    df[f"{codigo_acao}_tendencia_CP"],
    label=f"{codigo_acao} - Linha de Tendência",
)

# Adicionar a seta no final da linha de tendência
plt.arrow(
    df[f"{codigo_acao}_tendencia_LP"].iloc[-2],
    df[f"{codigo_acao}_tendencia_CP"].iloc[-2],
    df[f"{codigo_acao}_tendencia_LP"].iloc[-1]
    - df[f"{codigo_acao}_tendencia_LP"].iloc[-2],
    df[f"{codigo_acao}_tendencia_CP"].iloc[-1]
    - df[f"{codigo_acao}_tendencia_CP"].iloc[-2],
    shape="full",
    color="red",
    lw=1,
    length_includes_head=True,
    head_width=0.1,
)




# Color each quadrant
plt.fill_between([96, 100], [96, 96], [100, 100], color="red", alpha=0.2)
plt.fill_between([100, 104], [96, 96], [100, 100], color="yellow", alpha=0.2)
plt.fill_between([104, 100], [100, 100], [104, 104], color="green", alpha=0.2)
plt.fill_between([100, 96], [104, 104], [100, 100], color="blue", alpha=0.2)
# Add text labels in each corner
plt.text(98, 102, "Improving")
plt.text(102, 102, "Leading")
plt.text(102, 98, "Weakening")
plt.text(98, 98, "Lagging")


plt.axhline(100, color="black", linestyle="--", linewidth=0.8)
plt.axvline(100, color="black", linestyle="--", linewidth=0.8)
plt.title("Relative Rotation Graph")
plt.xlabel(f"RS")
plt.ylabel(f"Momentum")
plt.legend()
plt.grid(True)
plt.show()
