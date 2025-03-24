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

# Diretório onde os arquivos CSV estão armazenados
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
# Processamento de Cada Ativo
# -------------------------------
results = []
rolling_window = 21
smoothing_span = 9

fig = go.Figure()

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

    theta_final = smoothed_theta.iloc[-1]
    rotation_final = smoothed_rotation.iloc[-1]

    # Determinação do quadrante
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

    # Cálculo do ângulo do movimento para determinar a direção cardinal
    dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
    dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
    angle_movement = math.degrees(math.atan2(dy, dx))
    direcao = get_cardinal_direction(angle_movement)

    # Cálculo da variação do momentum (diferença entre os dois últimos valores suavizados de rotação)
    var_momentum = ((smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2])/abs(smoothed_rotation.iloc[-2]))*100

    # Cálculo da distância em relação ao centro (assumindo centro em (0,0))
    distancia = math.sqrt(theta_final**2 + rotation_final**2)

    results.append({
        "Ação": codigo_acao,
        "Quadrante": quadrante,
        "Direção": direcao,
        "Theta": round(theta_final, 2),
        "Rotação": round(rotation_final, 2),
        "Variação_Momentum": round(var_momentum, 2),
        "Distância": round(distancia, 2)
    })

    fig.add_trace(go.Scatter(x=smoothed_theta, y=smoothed_rotation, mode="lines+markers",
                             marker=dict(size=6), name=codigo_acao))

# Configuração do gráfico Plotly
fig.update_layout(title=f"RRG – {indice}", xaxis_title="Theta (graus)",
                  yaxis_title="Rotação (graus)", showlegend=True, plot_bgcolor="white")
fig.show()

# Salvar os resultados em Excel
if results:
    df_resultados = pd.DataFrame(results)
    output_excel = f"RRG_{indice}.xlsx"
    df_resultados.to_excel(output_excel, index=False)
    print(f"Arquivo Excel '{output_excel}' criado com sucesso!")
else:
    print("Nenhum resultado foi processado.")
