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
    Mapeia um ângulo (em graus) para uma direção cardinal com 8 possibilidades:
      - leste:     (-22.5, 22.5]
      - nordeste:  (22.5, 67.5]
      - norte:     (67.5, 112.5]
      - noroeste:  (112.5, 157.5]
      - oeste:     (angle > 157.5 ou <= -157.5)
      - sudoeste:  (-157.5, -112.5]
      - sul:       (-112.5, -67.5]
      - sudeste:   (-67.5, -22.5]
    """
    if -22.5 < angle <= 22.5:
        return "leste"
    elif 22.5 < angle <= 67.5:
        return "nordeste"
    elif 67.5 < angle <= 112.5:
        return "norte"
    elif 112.5 < angle <= 157.5:
        return "noroeste"
    elif angle > 157.5 or angle <= -157.5:
        return "oeste"
    elif -157.5 < angle <= -112.5:
        return "sudoeste"
    elif -112.5 < angle <= -67.5:
        return "sul"
    elif -67.5 < angle <= -22.5:
        return "sudeste"
    else:
        return "indeterminado"

# -------------------------------
# Entrada do Usuário e Leitura dos Dados
# -------------------------------

# Solicita ao usuário o código da ação
codigo_acao = input("Digite o código da ação: ").strip()

# Diretório onde os arquivos CSV estão armazenados
data_dir = r"C:/Users/armen/OneDrive/Estratégias/Base/Diária"

# Caminho do arquivo da ação e do benchmark (Ibovespa)
asset_file = os.path.join(data_dir, f"{codigo_acao}_B_0_Diário.csv")
benchmark_file = os.path.join(data_dir, "IBOV_B_0_Diário.csv")

if not os.path.exists(asset_file):
    print(f"Arquivo da ação {codigo_acao} não encontrado!")
    exit()

if not os.path.exists(benchmark_file):
    print("Arquivo do IBOV não encontrado!")
    exit()

# Leitura dos dados da ação
acao = pd.read_csv(asset_file,
                   sep=";",
                   encoding="ISO-8859-1",
                   skiprows=0,
                   skipfooter=2,
                   engine="python",
                   thousands=".",
                   decimal=",",
                   header=0)

# Monta o DataFrame com Data e Fechamento da Ação
dados = pd.DataFrame()
dados["Data"] = pd.to_datetime(acao["Data"], format="%d/%m/%Y")
dados["Ação"] = acao["Fechamento"]
dados = dados.sort_values(by="Data", ascending=True)

# Leitura dos dados do benchmark (Ibovespa)
ibov = pd.read_csv(benchmark_file,
                   sep=";",
                   encoding="ISO-8859-1",
                   skiprows=0,
                   skipfooter=2,
                   engine="python",
                   thousands=".",
                   decimal=",",
                   header=0)
ibov["Data"] = pd.to_datetime(ibov["Data"], format="%d/%m/%Y")
ibov = ibov.sort_values(by="Data", ascending=True)

# Realiza o merge dos dados da ação com os do benchmark com base na Data
merged = pd.merge(dados, ibov[["Data", "Fechamento"]], on="Data", how="inner")
merged.rename(columns={"Fechamento": "Indice"}, inplace=True)

if merged.empty:
    print("Dados vazios após merge com o benchmark!")
    exit()

# -------------------------------
# Cálculo das Funções Reais do RRG
# -------------------------------
merged["RS"] = merged["Ação"] / merged["Indice"]
merged["logRS"] = np.log(merged["RS"])

# Parâmetro para a janela do cálculo do rolling slope
rolling_window = 30
merged["slope"] = merged["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
merged["theta"] = np.degrees(np.arctan(merged["slope"]))
merged["rotation"] = merged["theta"].diff()

merged_clean = merged.dropna(subset=["theta", "rotation"]).reset_index(drop=True)

# Seleciona os últimos 10 dias
dados_last10 = merged_clean.tail(10)
if len(dados_last10) < 2:
    print("Dados insuficientes (menos de 10 dias)!")
    exit()

# -------------------------------
# Suavização da "Calda" (últimos 10 dias)
# -------------------------------
# Parâmetro para suavização (média móvel exponencial)
smoothing_span = 3
smoothed_theta = dados_last10["theta"].ewm(span=smoothing_span, adjust=False).mean()
smoothed_rotation = dados_last10["rotation"].ewm(span=smoothing_span, adjust=False).mean()

# Valores finais suavizados
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
# Utiliza a variação entre os dois últimos pontos suavizados
dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
angle_movement = math.degrees(math.atan2(dy, dx))
direcao = get_cardinal_direction(angle_movement)

# Exibe os resultados
print(f"\nResultados para a ação {codigo_acao} (últimos 10 dias, suavizados):")
print(f"Quadrante: {quadrante}")
print(f"Direção: {direcao}")
print(f"Theta (graus): {round(theta_final, 2)}")
print(f"Rotação (graus): {round(rotation_final, 2)}")

# -------------------------------
# Geração do Arquivo Excel com os Resultados
# -------------------------------
df_resultado = pd.DataFrame({
    "Ação": [codigo_acao],
    "Quadrante": [quadrante],
    "Direção": [direcao],
    "Theta (graus)": [round(theta_final, 2)],
    "Rotação (graus)": [round(rotation_final, 2)]
})
output_excel = f"{codigo_acao}_quadrante_direcao.xlsx"
df_resultado.to_excel(output_excel, index=False)
print(f"\nArquivo Excel '{output_excel}' criado com sucesso!")

# -------------------------------
# (Opcional) Criação do Gráfico RRG com Plotly
# -------------------------------
# Define os limites dos eixos com base nos dados suavizados
min_theta = min(smoothed_theta.min(), -0.5)
max_theta = max(smoothed_theta.max(), 0.5)
min_rotation = min(smoothed_rotation.min(), -0.5)
max_rotation = max(smoothed_rotation.max(), 0.5)

fig = go.Figure()

# Preenchimento dos quadrantes
fig.add_shape(type="rect",
              x0=min_theta, x1=0, y0=0, y1=max_rotation,
              fillcolor="blue", opacity=0.2, line=dict(width=0))
fig.add_shape(type="rect",
              x0=0, x1=max_theta, y0=0, y1=max_rotation,
              fillcolor="green", opacity=0.2, line=dict(width=0))
fig.add_shape(type="rect",
              x0=0, x1=max_theta, y0=min_rotation, y1=0,
              fillcolor="yellow", opacity=0.2, line=dict(width=0))
fig.add_shape(type="rect",
              x0=min_theta, x1=0, y0=min_rotation, y1=0,
              fillcolor="red", opacity=0.2, line=dict(width=0))

# Linhas de referência (eixos zero)
fig.add_shape(type="line", x0=min_theta, x1=max_theta, y0=0, y1=0, line=dict(color="gray", dash="dash"))
fig.add_shape(type="line", x0=0, x1=0, y0=min_rotation, y1=max_rotation, line=dict(color="gray", dash="dash"))

# Trajetória (a "calda") dos últimos 10 dias suavizados
fig.add_trace(go.Scatter(
    x=smoothed_theta,
    y=smoothed_rotation,
    mode="lines+markers",
    marker=dict(size=6),
    name=codigo_acao
))

# Ponto final destacado
fig.add_trace(go.Scatter(
    x=[theta_final],
    y=[rotation_final],
    mode="markers",
    marker=dict(size=10, color="black"),
    name="Último Ponto"
))

# Anotação da direção no ponto final
fig.add_annotation(
    x=theta_final,
    y=rotation_final,
    text=f"{direcao} - {codigo_acao}",
    showarrow=True,
    arrowhead=2,
    font=dict(size=12, color="red"),
    ax=0,
    ay=-20
)

fig.update_layout(
    title=f"RRG – Relative Rotation Graph (Últimos 10 dias, suavizados): {codigo_acao}",
    xaxis_title="Theta (graus)",
    yaxis_title="Rotação (graus)",
    xaxis=dict(range=[min_theta, max_theta], zeroline=True),
    yaxis=dict(range=[min_rotation, max_rotation], zeroline=True),
    showlegend=True,
    plot_bgcolor="white"
)

fig.show()
