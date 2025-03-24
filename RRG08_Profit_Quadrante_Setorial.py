import os
import math
import glob
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# -------------------------------
# Função para regressão linear em janela móvel
# -------------------------------
def rolling_slope(x):
    t = np.arange(len(x))
    slope, _ = np.polyfit(t, x, 1)
    return slope


# -------------------------------
# Função para mapear ângulo em direção cardinal
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
# Seleção do Benchmark e Lista de Ativos
# -------------------------------
data_dir = r"C:/Estrategia/Base/Diaria/"
ativos = ["SMLL", "IEEX", "INDX", "IMAT", "ICON", "UTIL", "IFNC", "IMOB"]

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
# Mapeamento de cores para os quadrantes RRG
# -------------------------------
# FORTE: theta > 0 e rotação > 0 (Quadrante superior direito)
# ENFRAQUECENDO: theta > 0 e rotação < 0 (Quadrante inferior direito)
# FRACO: theta < 0 e rotação < 0 (Quadrante inferior esquerdo)
# FORTALECENDO: theta < 0 e rotação > 0 (Quadrante superior esquerdo)
cores_quadrantes = {
    "FORTE": "green",
    "ENFRAQUECENDO": "orange",
    "FRACO": "red",
    "FORTALECENDO": "blue"
}

# -------------------------------
# Processamento de Cada Ativo
# -------------------------------
results = []
rolling_window = 21
smoothing_span = 9

fig = go.Figure()

# Listas para armazenar os valores de theta e rotação de todos os ativos
all_theta = []
all_rotation = []

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
    merged.rename(columns={"Fechamento_x": "Ação", "Fechamento_y": "Indice"}, inplace=True)

    if merged.empty:
        print(f"Dados vazios para {codigo_acao}, pulando...")
        continue

    merged["RS"] = merged["Ação"] / merged["Indice"]
    merged["logRS"] = np.log(merged["RS"])
    merged["slope"] = merged["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
    merged["theta"] = np.degrees(np.arctan(merged["slope"]))
    merged["rotation"] = merged["theta"].diff()

    merged_clean = merged.dropna(subset=["theta", "rotation"]).reset_index(drop=True)
    dados_last10 = merged_clean.tail(10)

    if len(dados_last10) < 2:
        print(f"Dados insuficientes para {codigo_acao}, pulando...")
        continue

    smoothed_theta = dados_last10["theta"].ewm(span=smoothing_span, adjust=False).mean()
    smoothed_rotation = dados_last10["rotation"].ewm(span=smoothing_span, adjust=False).mean()

    # Acumula os valores para definir os limites do gráfico
    all_theta.extend(smoothed_theta.tolist())
    all_rotation.extend(smoothed_rotation.tolist())

    theta_final = smoothed_theta.iloc[-1]
    rotation_final = smoothed_rotation.iloc[-1]

    # Determinação do quadrante
    if theta_final > 0 and rotation_final > 0:
        quadrante = "FORTE"
    elif theta_final > 0 and rotation_final < 0:
        quadrante = "ENFRAQUECENDO"
    elif theta_final < 0 and rotation_final < 0:
        quadrante = "FRACO"
    elif theta_final < 0 and rotation_final > 0:
        quadrante = "FORTALECENDO"
    else:
        quadrante = "Indeterminado"

    # Cálculo do ângulo do movimento para determinar a direção cardinal
    dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
    dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
    angle_movement = math.degrees(math.atan2(dy, dx))
    direcao = get_cardinal_direction(angle_movement)

    # Cálculo da variação do momentum (diferença entre os dois últimos valores suavizados de rotação)
    var_momentum = ((smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]) / abs(smoothed_rotation.iloc[-2])) * 100

    # Cálculo da distância em relação ao centro (assumindo centro em (0,0))
    distancia = math.sqrt(theta_final ** 2 + rotation_final ** 2)

    results.append({
        "Ação": codigo_acao,
        "Quadrante": quadrante,
        "Direção": direcao,
        "Theta": round(theta_final, 2),
        "Rotação": round(rotation_final, 2),
        "Variação_Momentum": round(var_momentum, 2),
        "Distância": round(distancia, 2)
    })

    # Plotagem do ativo sem legenda
    fig.add_trace(go.Scatter(
        x=smoothed_theta,
        y=smoothed_rotation,
        mode="lines+markers",
        marker=dict(size=6),
        showlegend=False  # Remove a legenda
    ))

    # Adiciona uma anotação com o código do ativo próximo ao último ponto
    fig.add_annotation(
        x=smoothed_theta.iloc[-1],
        y=smoothed_rotation.iloc[-1],
        ax=smoothed_theta.iloc[-2],
        ay=smoothed_rotation.iloc[-2],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="black",
        text=codigo_acao,
        font=dict(color="black", size=12),
        xanchor="left",
        yanchor="middle"
    )

# Verifica se houve algum dado processado
if not results:
    print("Nenhum resultado foi processado.")
    exit()

# Converte as listas para arrays e calcula os limites dos eixos com base nos dados,
# garantindo que o zero esteja incluído
all_theta = np.array(all_theta)
all_rotation = np.array(all_rotation)

x_min = min(all_theta.min(), 0)
x_max = max(all_theta.max(), 0)
y_min = min(all_rotation.min(), 0)
y_max = max(all_rotation.max(), 0)

# Calcula uma margem de 10% para os limites
x_margin = (x_max - x_min) * 0.1
y_margin = (y_max - y_min) * 0.1

x_range = [x_min - x_margin, x_max + x_margin]
y_range = [y_min - y_margin, y_max + y_margin]

# Adiciona shapes para os quadrantes com base nos limites calculados
shapes = [
    # Quadrante FORTE (theta > 0 e rotação > 0)
    dict(
        type="rect",
        xref="x", yref="y",
        x0=0, y0=0,
        x1=x_range[1], y1=y_range[1],
        fillcolor=cores_quadrantes["FORTE"],
        opacity=0.2,
        layer="below",
        line_width=0,
    ),
    # Quadrante ENFRAQUECENDO (theta > 0 e rotação < 0)
    dict(
        type="rect",
        xref="x", yref="y",
        x0=0, y0=y_range[0],
        x1=x_range[1], y1=0,
        fillcolor=cores_quadrantes["ENFRAQUECENDO"],
        opacity=0.2,
        layer="below",
        line_width=0,
    ),
    # Quadrante FRACO (theta < 0 e rotação < 0)
    dict(
        type="rect",
        xref="x", yref="y",
        x0=x_range[0], y0=y_range[0],
        x1=0, y1=0,
        fillcolor=cores_quadrantes["FRACO"],
        opacity=0.2,
        layer="below",
        line_width=0,
    ),
    # Quadrante FORTALECENDO (theta < 0 e rotação > 0)
    dict(
        type="rect",
        xref="x", yref="y",
        x0=x_range[0], y0=0,
        x1=0, y1=y_range[1],
        fillcolor=cores_quadrantes["FORTALECENDO"],
        opacity=0.2,
        layer="below",
        line_width=0,
    )
]

fig.update_layout(
    title="RRS dos Setores",
    xaxis_title="Força Relativa",
    yaxis_title="Momentum Relativo",
    plot_bgcolor="white",
    shapes=shapes,
    xaxis=dict(range=x_range, zeroline=True),
    yaxis=dict(range=y_range, zeroline=True)
)

fig.show()

# Salva os resultados em um arquivo Excel
df_resultados = pd.DataFrame(results)
output_excel = "RRG_Carteira.xlsx"
df_resultados.to_excel(output_excel, index=False)
print(f"Arquivo Excel '{output_excel}' criado com sucesso!")
