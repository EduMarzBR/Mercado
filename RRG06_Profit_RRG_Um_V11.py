import os
import math
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
# Solicitar o código da ação
# -------------------------------
codigo_acao = input("Digite o código da ação desejada: ").strip()

# Diretório onde os arquivos CSV estão armazenados
data_dir = r"C:/Estrategia/Base/Diaria/"

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
# Leitura dos dados da ação
# -------------------------------
asset_file = os.path.join(data_dir, f"{codigo_acao}_B_0_Diário.csv")
if not os.path.exists(asset_file):
    print(f"Arquivo da ação {codigo_acao} não encontrado!")
    exit()

acao = pd.read_csv(asset_file, sep=";", encoding="ISO-8859-1", skiprows=0,
                   skipfooter=2, engine="python", thousands=".", decimal=",",
                   header=0)
acao["Data"] = pd.to_datetime(acao["Data"], format="%d/%m/%Y")
acao = acao.sort_values(by="Data", ascending=True)

# -------------------------------
# Merge entre ação e benchmark
# -------------------------------
merged = pd.merge(acao, ibov[["Data", "Fechamento"]], on="Data", how="inner")
merged.rename(columns={"Fechamento_x": "Ação", "Fechamento_y": "Indice"}, inplace=True)

if merged.empty:
    print("Não há dados em comum entre a ação e o benchmark.")
    exit()

# -------------------------------
# Cálculos do RRG
# -------------------------------
merged["RS"] = merged["Ação"] / merged["Indice"]
merged["logRS"] = np.log(merged["RS"])

rolling_window = 21
smoothing_span = 9

merged["slope"] = merged["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
merged["theta"] = np.degrees(np.arctan(merged["slope"]))
merged["rotation"] = merged["theta"].diff()

merged_clean = merged.dropna(subset=["theta", "rotation"]).reset_index(drop=True)
dados_last10 = merged_clean.tail(10)

if len(dados_last10) < 2:
    print("Dados insuficientes para calcular o RRG.")
    exit()

smoothed_theta = dados_last10["theta"].ewm(span=smoothing_span, adjust=False).mean()
smoothed_rotation = dados_last10["rotation"].ewm(span=smoothing_span, adjust=False).mean()

theta_final = smoothed_theta.iloc[-1]
rotation_final = smoothed_rotation.iloc[-1]

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

dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
angle_movement = math.degrees(math.atan2(dy, dx))
direcao = get_cardinal_direction(angle_movement)

# -------------------------------
# Exibir Resultados
# -------------------------------
print(f"\nRRG da Ação: {codigo_acao}")
print(f"Quadrante: {quadrante}")
print(f"Direção: {direcao}")
print(f"Theta: {round(theta_final, 2)}")
print(f"Rotação: {round(rotation_final, 2)}")

# -------------------------------
# Gráfico RRG com Plotly e cores dos quadrantes
# -------------------------------
fig = go.Figure()

# Adiciona a linha da evolução dos valores
fig.add_trace(go.Scatter(x=smoothed_theta, y=smoothed_rotation, mode="lines+markers",
                         marker=dict(size=6), name=codigo_acao))

# Calcula os limites simétricos para os eixos
margin = 0.5
abs_theta = max(abs(smoothed_theta.min()), abs(smoothed_theta.max()), margin)
abs_rot = max(abs(smoothed_rotation.min()), abs(smoothed_rotation.max()), margin)
theta_min = -abs_theta
theta_max = abs_theta
rot_min = -abs_rot
rot_max = abs_rot

# Configura os retângulos para colorir os quadrantes
shapes = [
    # Quadrante FORTE (theta > 0 e rotação > 0) - Verde
    dict(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=0,
        x1=theta_max,
        y1=rot_max,
        fillcolor="rgba(0, 255, 0, 0.2)",
        line=dict(width=0),
        layer="below"
    ),
    # Quadrante ENFRAQUECENDO (theta > 0 e rotação < 0) - Amarelo
    dict(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=rot_min,
        x1=theta_max,
        y1=0,
        fillcolor="rgba(255, 255, 0, 0.2)",
        line=dict(width=0),
        layer="below"
    ),
    # Quadrante FRACO (theta < 0 e rotação < 0) - Vermelho
    dict(
        type="rect",
        xref="x",
        yref="y",
        x0=theta_min,
        y0=rot_min,
        x1=0,
        y1=0,
        fillcolor="rgba(255, 0, 0, 0.2)",
        line=dict(width=0),
        layer="below"
    ),
    # Quadrante FORTALECENDO (theta < 0 e rotação > 0) - Azul
    dict(
        type="rect",
        xref="x",
        yref="y",
        x0=theta_min,
        y0=0,
        x1=0,
        y1=rot_max,
        fillcolor="rgba(0, 0, 255, 0.2)",
        line=dict(width=0),
        layer="below"
    ),
    # Linha vertical no eixo theta=0
    dict(
        type="line",
        xref="x",
        yref="y",
        x0=0,
        y0=rot_min,
        x1=0,
        y1=rot_max,
        line=dict(color="black", width=1, dash="dash"),
        layer="above"
    ),
    # Linha horizontal no eixo rotação=0
    dict(
        type="line",
        xref="x",
        yref="y",
        x0=theta_min,
        y0=0,
        x1=theta_max,
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
        layer="above"
    )
]

fig.update_layout(
    title=f"RRG – {codigo_acao}",
    xaxis_title="Força Relativa",
    yaxis_title="Momentum Relativo",
    showlegend=True,
    plot_bgcolor="white",
    shapes=shapes
)

# Adiciona a seta indicando a direção do movimento (do penúltimo para o último ponto)
fig.add_annotation(
    x=smoothed_theta.iloc[-1],
    y=smoothed_rotation.iloc[-1],
    ax=smoothed_theta.iloc[-2],
    ay=smoothed_rotation.iloc[-2],
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    text="",
    showarrow=True,
    arrowhead=3,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="black"
)

# Adiciona anotações com os nomes de todos os quadrantes, posicionados no centro de cada área
fig.add_annotation(
    x=(0 + theta_max) / 2,
    y=(0 + rot_max) / 2,
    text="FORTE",
    showarrow=False,
    font=dict(color="black", size=12)
)
fig.add_annotation(
    x=(0 + theta_max) / 2,
    y=(rot_min + 0) / 2,
    text="ENFRAQUECENDO",
    showarrow=False,
    font=dict(color="black", size=12)
)
fig.add_annotation(
    x=(theta_min + 0) / 2,
    y=(rot_min + 0) / 2,
    text="FRACO",
    showarrow=False,
    font=dict(color="black", size=12)
)
fig.add_annotation(
    x=(theta_min + 0) / 2,
    y=(0 + rot_max) / 2,
    text="FORTALECENDO",
    showarrow=False,
    font=dict(color="black", size=12)
)

fig.show()

# -------------------------------
# Salvar os resultados em Excel
# -------------------------------
df_resultados = pd.DataFrame([{
    "Ação": codigo_acao,
    "Quadrante": quadrante,
    "Direção": direcao,
    "Theta": round(theta_final, 2),
    "Rotação": round(rotation_final, 2)
}])
# output_excel = f"RRG_{codigo_acao}.xlsx"
# df_resultados.to_excel(output_excel, index=False)
# print(f"Arquivo Excel '{output_excel}' criado com sucesso!")
