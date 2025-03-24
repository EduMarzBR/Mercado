import os
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# -------------------------------
# Função para regressão linear em janela móvel
# -------------------------------
def rolling_slope(x):
    """
    Calcula a inclinação (slope) da regressão linear para um array x,
    utilizando os índices (0, 1, ..., len(x)-1) como variável independente.
    """
    t = np.arange(len(x))
    slope, _ = np.polyfit(t, x, 1)
    return slope

# -------------------------------
# Função para mapear ângulo em direção cardinal
# -------------------------------
def get_cardinal_direction(angle):
    """
    Mapeia um ângulo (em graus) para uma direção cardinal.
    """
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
# Entrada do Usuário e Leitura dos Dados
# -------------------------------
codigo_acao = input("Digite o código da ação: ").strip()
data_dir = r"C:/Estrategia/Base/Diaria/"

# Arquivos da ação e do benchmark (Ibovespa)
asset_file = os.path.join(data_dir, f"{codigo_acao}_B_0_Diário.csv")
benchmark_file = os.path.join(data_dir, "IBOV_B_0_Diário.csv")

# Verificação da existência dos arquivos
if not os.path.exists(asset_file):
    print(f"Arquivo da ação {codigo_acao} não encontrado!")
    exit()
if not os.path.exists(benchmark_file):
    print("Arquivo do IBOV não encontrado!")
    exit()

# Leitura dos dados da ação
acao = pd.read_csv(asset_file, sep=";", encoding="ISO-8859-1", skiprows=0, skipfooter=2,
                   engine="python", thousands=".", decimal=",", header=0)
acao["Data"] = pd.to_datetime(acao["Data"], format="%d/%m/%Y")
acao = acao.sort_values(by="Data")

# Leitura dos dados do benchmark (Ibovespa)
ibov = pd.read_csv(benchmark_file, sep=";", encoding="ISO-8859-1", skiprows=0, skipfooter=2,
                   engine="python", thousands=".", decimal=",", header=0)
ibov["Data"] = pd.to_datetime(ibov["Data"], format="%d/%m/%Y")
ibov = ibov.sort_values(by="Data")

# Merge dos dados da ação com o benchmark
merged = pd.merge(acao[["Data", "Fechamento"]], ibov[["Data", "Fechamento"]], on="Data", how="inner")
merged.rename(columns={"Fechamento_x": "Ação", "Fechamento_y": "Indice"}, inplace=True)

if merged.empty:
    print("Dados vazios após merge com o benchmark!")
    exit()

# -------------------------------
# Cálculo das Funções do RRG
# -------------------------------
rolling_window = 21  # Janela da regressão linear
smoothing_span = 9   # Parâmetro para suavização EMA

merged["RS"] = merged["Ação"] / merged["Indice"]
merged["logRS"] = np.log(merged["RS"])
merged["slope"] = merged["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
merged["theta"] = np.degrees(np.arctan(merged["slope"]))
merged["rotation"] = merged["theta"].diff()

# Suavização exponencial dos últimos 10 dias
merged_clean = merged.dropna(subset=["theta", "rotation"]).reset_index(drop=True)
dados_last10 = merged_clean.tail(10)

if len(dados_last10) < 2:
    print("Dados insuficientes (menos de 10 dias)!")
    exit()

smoothed_theta = dados_last10["theta"].ewm(span=smoothing_span, adjust=False).mean()*100
smoothed_rotation = dados_last10["rotation"].ewm(span=smoothing_span, adjust=False).mean() *100

# Valores finais
theta_final = smoothed_theta.iloc[-1]
rotation_final = smoothed_rotation.iloc[-1]

# -------------------------------
# Classificação do Quadrante
# -------------------------------
if theta_final > 0 and rotation_final > 0:
    quadrante = "Leading"
elif theta_final > 0 and rotation_final < 0:
    quadrante = "Weakening"
elif theta_final < 0 and rotation_final < 0:
    quadrante = "Lagging"
elif theta_final < 0 and rotation_final > 0:
    quadrante = "Improving"
else:
    quadrante = "Indeterminado"

# -------------------------------
# Cálculo da Direção
# -------------------------------
dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
angle_movement = math.degrees(math.atan2(dy, dx))
direcao = get_cardinal_direction(angle_movement)

# -------------------------------
# Criação do Gráfico RRG com Plotly
# -------------------------------
# Define os limites dos eixos com base nos dados suavizados
min_theta = min(smoothed_theta.min(), -0.5*100)
max_theta = max(smoothed_theta.max(), 0.5*100)
min_rotation = min(smoothed_rotation.min(), -0.5*100)
max_rotation = max(smoothed_rotation.max(), 0.5*100)

fig = go.Figure()

# Preenchimento dos quadrantes
fig.add_shape(type="rect", x0=min_theta, x1=0, y0=0, y1=max_rotation, fillcolor="blue", opacity=0.2, line=dict(width=0))
fig.add_shape(type="rect", x0=0, x1=max_theta, y0=0, y1=max_rotation, fillcolor="green", opacity=0.2, line=dict(width=0))
fig.add_shape(type="rect", x0=0, x1=max_theta, y0=min_rotation, y1=0, fillcolor="yellow", opacity=0.2, line=dict(width=0))
fig.add_shape(type="rect", x0=min_theta, x1=0, y0=min_rotation, y1=0, fillcolor="red", opacity=0.2, line=dict(width=0))

# Linhas de referência (eixos zero)
fig.add_shape(type="line", x0=min_theta, x1=max_theta, y0=0, y1=0, line=dict(color="gray", dash="dash"))
fig.add_shape(type="line", x0=0, x1=0, y0=min_rotation, y1=max_rotation, line=dict(color="gray", dash="dash"))

# Trajetória dos últimos 10 dias suavizados
fig.add_trace(go.Scatter(x=smoothed_theta, y=smoothed_rotation, mode="lines+markers", marker=dict(size=6), name=codigo_acao))

# Ponto final destacado
fig.add_trace(go.Scatter(x=[theta_final], y=[rotation_final], mode="markers", marker=dict(size=10, color="black"), name="Último Ponto"))

# Anotação da direção no ponto final
fig.add_annotation(x=theta_final, y=rotation_final, text=f"{direcao} - {codigo_acao}", showarrow=True, arrowhead=2, font=dict(size=12, color="red"), ax=0, ay=-20)

fig.update_layout(title=f"RRG – {codigo_acao}", xaxis_title="Theta (graus)", yaxis_title="Rotação (graus)", showlegend=True, plot_bgcolor="white")

fig.show()
