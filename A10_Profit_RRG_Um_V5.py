import plotly.graph_objects as go
import math
import os
import numpy as np
import pandas as pd

# -------------------------------
# Função para regressão linear em janela móvel
# -------------------------------
def rolling_slope(x):
    """
    Calcula a inclinação (slope) da regressão linear para o array x,
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
codigo_acao = input("Digite o código da ação: ").strip()

# Caminhos dos arquivos
arquivo_acao = f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{codigo_acao}_B_0_Diário.csv"
arquivo_ibov = f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/IBOV_B_0_Diário.csv"

if not os.path.exists(arquivo_acao):
    print(f"Arquivo da ação {codigo_acao} não encontrado!")
    exit()

if not os.path.exists(arquivo_ibov):
    print("Arquivo do IBOV não encontrado!")
    exit()

# Leitura dos arquivos (ajuste os parâmetros conforme necessário)
acao = pd.read_csv(arquivo_acao,
                   sep=";",
                   encoding="ISO-8859-1",
                   skiprows=0,
                   skipfooter=2,
                   engine="python",
                   thousands=".",
                   decimal=",",
                   header=0)

ibov = pd.read_csv(arquivo_ibov,
                   sep=";",
                   encoding="ISO-8859-1",
                   skiprows=0,
                   skipfooter=2,
                   engine="python",
                   thousands=".",
                   decimal=",",
                   header=0)

# Monta o DataFrame unificando os dados: Data, Fechamento da Ação e Fechamento do Índice
dados = pd.DataFrame()
dados["Data"] = acao["Data"]
dados["Ação"] = acao["Fechamento"]
dados["Indice"] = ibov["Fechamento"]
dados["Data"] = pd.to_datetime(dados["Data"], format="%d/%m/%Y")
dados = dados.sort_values(by="Data", ascending=True)

# -------------------------------
# Cálculo das Funções Reais do RRG
# -------------------------------

# 1. Cálculo da Força Relativa (RS) e transformação logarítmica
dados["RS"] = dados["Ação"] / dados["Indice"]
dados["logRS"] = np.log(dados["RS"])

# 2. Regressão linear móvel para extrair a tendência
rolling_window = 30  # ajuste o tamanho da janela conforme necessário
dados["slope"] = dados["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)

# 3. Conversão da inclinação em ângulo (θ) em graus
dados["theta"] = np.degrees(np.arctan(dados["slope"]))

# 4. Cálculo da rotação (diferença diária de θ)
dados["rotation"] = dados["theta"].diff()

# Remover os pontos sem dados (resultantes do rolling e diff)
dados_clean = dados.dropna(subset=["theta", "rotation"]).reset_index(drop=True)

# Filtra apenas os últimos 10 dias
dados_last10 = dados_clean.tail(10)

# -------------------------------
# Classificação do Quadrante e Direção do Movimento (último ponto dos 10 dias)
# -------------------------------
theta_final = dados_last10["theta"].iloc[-1]
rotation_final = dados_last10["rotation"].iloc[-1]

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

# Calcula a direção com base na variação entre os dois últimos pontos dos 10 dias
if len(dados_last10) >= 2:
    dx = dados_last10["theta"].iloc[-1] - dados_last10["theta"].iloc[-2]
    dy = dados_last10["rotation"].iloc[-1] - dados_last10["rotation"].iloc[-2]
    angle_movement = math.degrees(math.atan2(dy, dx))
    direcao = get_cardinal_direction(angle_movement)
else:
    direcao = "Indeterminado"

print(f"\nResultados para a ação {codigo_acao} (últimos 10 dias):")
print(f"Quadrante: {quadrante}")
print(f"Direção: {direcao}")

# -------------------------------
# Geração do Arquivo Excel com o Resultado
# -------------------------------
df_resultado = pd.DataFrame({
    "Ação": [codigo_acao],
    "Quadrante": [quadrante],
    "Direção": [direcao],
    "Theta (graus)": [round(theta_final, 2)],
    "Rotação (graus)": [round(rotation_final, 2)]
})

arquivo_excel = "acao_quadrante_direcao.xlsx"
df_resultado.to_excel(arquivo_excel, index=False)
print(f"\nArquivo Excel '{arquivo_excel}' criado com sucesso!")

# -------------------------------
# Criação do Gráfico RRG com Plotly (apenas últimos 10 dias)
# -------------------------------

# Definindo os limites dos eixos com base nos dados dos últimos 10 dias (com margem)
min_theta = min(dados_last10["theta"].min(), -0.5)
max_theta = max(dados_last10["theta"].max(), 0.5)
min_rotation = min(dados_last10["rotation"].min(), -0.5)
max_rotation = max(dados_last10["rotation"].max(), 0.5)

fig = go.Figure()

# Preenche os quadrantes:
# Improving: theta < 0 e rotation > 0 (superior esquerdo)
fig.add_shape(type="rect",
              x0=min_theta, x1=0, y0=0, y1=max_rotation,
              fillcolor="blue", opacity=0.2, line=dict(width=0))
# Leading: theta > 0 e rotation > 0 (superior direito)
fig.add_shape(type="rect",
              x0=0, x1=max_theta, y0=0, y1=max_rotation,
              fillcolor="green", opacity=0.2, line=dict(width=0))
# Weakening: theta > 0 e rotation < 0 (inferior direito)
fig.add_shape(type="rect",
              x0=0, x1=max_theta, y0=min_rotation, y1=0,
              fillcolor="yellow", opacity=0.2, line=dict(width=0))
# Lagging: theta < 0 e rotation < 0 (inferior esquerdo)
fig.add_shape(type="rect",
              x0=min_theta, x1=0, y0=min_rotation, y1=0,
              fillcolor="red", opacity=0.2, line=dict(width=0))

# Linhas de referência (eixos zero)
fig.add_shape(type="line", x0=min_theta, x1=max_theta, y0=0, y1=0, line=dict(color="gray", dash="dash"))
fig.add_shape(type="line", x0=0, x1=0, y0=min_rotation, y1=max_rotation, line=dict(color="gray", dash="dash"))

# Trajetória (a "calda") dos últimos 10 dias
fig.add_trace(go.Scatter(
    x=dados_last10["theta"],
    y=dados_last10["rotation"],
    mode="lines+markers",
    marker=dict(size=6),
    name=codigo_acao
))

# Ponto final destacado (último dos 10 dias)
fig.add_trace(go.Scatter(
    x=[theta_final],
    y=[rotation_final],
    mode="markers",
    marker=dict(size=10, color="black"),
    name="Último Ponto"
))

# Anotação da direção do movimento no ponto final
fig.add_annotation(
    x=theta_final, y=rotation_final,
    text=f"{direcao} - {codigo_acao}",
    showarrow=True,
    arrowhead=2,
    font=dict(size=12, color="red"),
    ax=0, ay=-20
)

# Configuração do layout do gráfico
fig.update_layout(
    title=f"RRG – Relative Rotation Graph (Últimos 10 dias): {codigo_acao}",
    xaxis_title="Theta (graus)",
    yaxis_title="Rotação (graus)",
    xaxis=dict(range=[min_theta, max_theta], zeroline=True),
    yaxis=dict(range=[min_rotation, max_rotation], zeroline=True),
    showlegend=True,
    plot_bgcolor="white"
)

# Exibe o gráfico interativo
fig.show()
