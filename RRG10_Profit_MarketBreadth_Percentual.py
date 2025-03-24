import os
import math
import glob
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# -------------------------------
# Função para regressão linear em janela móvel
# -------------------------------
def rolling_slope(x):
    t = np.arange(len(x))
    slope, _ = np.polyfit(t, x, 1)
    return slope

# -------------------------------
# Função para mapear ângulo em direção cardinal (mantida para referência)
# -------------------------------
def get_cardinal_direction(angle):
    if -22.5 < angle <= 22.5:
        return "Leste"
    elif 22.5 < angle <= 67.5:
        return "Nordeste"
    elif 67.5 < angle <= 112.5:
        return "Norte"
    elif 112.5 < angle <= 157.5:
        return "Noroeste"
    elif angle > 157.5 or angle <= -157.5:
        return "Oeste"
    elif -157.5 < angle <= -112.5:
        return "Sudoeste"
    elif -112.5 < angle <= -67.5:
        return "Sul"
    elif -67.5 < angle <= -22.5:
        return "Sudeste"
    else:
        return "Indeterminado"

# -------------------------------
# Função para determinar o quadrante do RRG com base em theta e rotação
# -------------------------------
def assign_quadrant(theta, rotation):
    if theta > 0 and rotation > 0:
        return "FORTE"
    elif theta > 0 and rotation < 0:
        return "ENFRAQUECENDO"
    elif theta < 0 and rotation < 0:
        return "FRACO"
    elif theta < 0 and rotation > 0:
        return "FORTALECENDO"
    else:
        return "Indeterminado"

# -------------------------------
# Seleção do Benchmark e Lista de Ativos
# -------------------------------
print("Escolha um índice:")
indices = {
    1: "IBOV", 2: "IBRA", 3: "BDRX", 4: "ICON", 5: "IDIV", 6: "IEEX",
    7: "IFIX", 8: "IFNC", 9: "IMAT", 10: "IMOB", 11: "INDX", 12: "MLCX",
    13: "SMLL", 14: "UTIL"
}
for k, v in indices.items():
    print(f"{k} - {v}")

codigo_indice = int(input("Digite o número do índice desejado: "))
if codigo_indice not in indices:
    print("Código de índice inválido.")
    exit()

indice = indices[codigo_indice]
print(f"Você selecionou o índice {indice}.")

# Diretórios dos dados
data_dir = r"C:/Estrategia/Base/Diaria/"
lista_dir = f"C:/Estrategia/Listas/{indice}/*"
list_of_files = glob.glob(lista_dir)

if not list_of_files:
    print(f"Nenhum arquivo encontrado para o índice {indice}.")
    exit()

latest_file = max(list_of_files, key=os.path.getctime)
lista = pd.read_csv(latest_file, sep=";", encoding="ISO-8859-1", skiprows=0,
                    skipfooter=2, engine="python", thousands=".", decimal=",",
                    header=1, index_col=False)
ativos = lista["Código"]

# -------------------------------
# Leitura do Benchmark (Ibovespa)
# -------------------------------
benchmark_file = os.path.join(data_dir, "IBOV_B_0_Diário.csv")
if not os.path.exists(benchmark_file):
    print("Arquivo do IBOV não encontrado!")
    exit()

ibov = pd.read_csv(benchmark_file, sep=";", encoding="ISO-8859-1", skiprows=0,
                   skipfooter=2, engine="python", thousands=".", decimal=",",
                   header=0)
ibov["Data"] = pd.to_datetime(ibov["Data"], format="%d/%m/%Y")
ibov = ibov.sort_values(by="Data", ascending=True)

# -------------------------------
# Processamento de Cada Ativo e extração da série de quadrantes
# -------------------------------
rolling_window = 21
smoothing_span = 9

lista_quadrantes = []

for codigo_acao in ativos:
    codigo_acao = str(codigo_acao).strip()
    asset_file = os.path.join(data_dir, f"{codigo_acao}_B_0_Diário.csv")

    if not os.path.exists(asset_file):
        print(f"Arquivo da ação {codigo_acao} não encontrado, pulando...")
        continue

    acao = pd.read_csv(asset_file, sep=";", encoding="ISO-8859-1", skiprows=0,
                       skipfooter=2, engine="python", thousands=".", decimal=",",
                       header=0)
    acao["Data"] = pd.to_datetime(acao["Data"], format="%d/%m/%Y")
    acao = acao.sort_values(by="Data", ascending=True)

    merged = pd.merge(acao, ibov[["Data", "Fechamento"]], on="Data", how="inner")
    if merged.empty:
        print(f"Dados vazios para {codigo_acao}, pulando...")
        continue

    merged.rename(columns={"Fechamento_x": "Ação", "Fechamento_y": "Indice"}, inplace=True)
    merged["RS"] = merged["Ação"] / merged["Indice"]
    merged["logRS"] = np.log(merged["RS"])

    merged["slope"] = merged["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
    merged["theta"] = np.degrees(merged["slope"])
    merged["rotation"] = merged["theta"].diff()

    merged_clean = merged.dropna(subset=["theta", "rotation"]).reset_index(drop=True)
    if merged_clean.empty:
        print(f"Dados insuficientes para {codigo_acao}, pulando...")
        continue

    merged_clean["smoothed_theta"] = merged_clean["theta"].ewm(span=smoothing_span, adjust=False).mean()
    merged_clean["smoothed_rotation"] = merged_clean["rotation"].ewm(span=smoothing_span, adjust=False).mean()

    merged_clean["Quadrante"] = merged_clean.apply(lambda row: assign_quadrant(row["smoothed_theta"],
                                                                              row["smoothed_rotation"]), axis=1)
    merged_clean["Ação"] = codigo_acao

    lista_quadrantes.append(merged_clean[["Data", "Quadrante", "Ação"]])

if not lista_quadrantes:
    print("Nenhum ativo foi processado.")
    exit()

df_quadrantes = pd.concat(lista_quadrantes)
df_quadrantes.sort_values("Data", inplace=True)

# -------------------------------
# Filtrar os últimos 12 meses (considerando o último dia disponível na base)
# -------------------------------
ultima_data = df_quadrantes["Data"].max()
data_inicio = ultima_data - timedelta(days=365)
df_12m = df_quadrantes[df_quadrantes["Data"] >= data_inicio].copy()

# -------------------------------
# Agregação: calcular o percentual de ações em cada quadrante por dia
# -------------------------------
df_contagem = df_12m.groupby(["Data", "Quadrante"])["Ação"].nunique().reset_index()
df_pivot = df_contagem.pivot(index="Data", columns="Quadrante", values="Ação").fillna(0)

# Cálculo do percentual para cada data
df_pct = df_pivot.div(df_pivot.sum(axis=1), axis=0) * 100

colunas_ordem = ["FORTALECENDO", "FORTE", "FRACO", "ENFRAQUECENDO"]
df_pct = df_pct.reindex(columns=colunas_ordem, fill_value=0)

# -------------------------------
# Plotando os resultados em gráficos separados (subplots) com Plotly
# -------------------------------
cores = {
    "FORTE": "green",
    "ENFRAQUECENDO": "orange",
    "FRACO": "red",
    "FORTALECENDO": "blue"
}

fig = make_subplots(rows=2, cols=2, subplot_titles=colunas_ordem)

posicoes = {
    "FORTE": (1, 2),
    "ENFRAQUECENDO": (2, 2),
    "FRACO": (2, 1),
    "FORTALECENDO": (1, 1)
}

for quadrante in colunas_ordem:
    if quadrante in df_pct.columns:
        row, col = posicoes[quadrante]
        fig.add_trace(
            go.Scatter(
                x=df_pct.index,
                y=df_pct[quadrante],
                mode="lines",
                name=quadrante,
                line=dict(color=cores.get(quadrante, "black"))
            ),
            row=row, col=col
        )
        last_date = df_pct.index[-1]
        last_value = df_pct[quadrante].iloc[-1]
        # Anotação destacada com fonte maior, fundo e borda, exibindo o percentual
        fig.add_annotation(
            x=last_date,
            y=last_value,
            text=f"<b>{last_value:.1f}%</b>",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-30,
            row=row, col=col,
            font=dict(color="white", size=16),
            bgcolor=cores.get(quadrante, "black"),
            bordercolor="black",
            borderwidth=2
        )

fig.update_layout(1
    plot_bgcolor="white",
    autosize=True,
    margin=dict(l=20, r=20, t=50, b=20)
)

fig.show(config={'responsive': True})
