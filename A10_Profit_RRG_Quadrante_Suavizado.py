import glob
import os
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go  # Apenas se desejar visualizar os gráficos

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
# Seleção do Benchmark e Lista de Ativos
# -------------------------------

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
codigo_indice = int(input("Digite o número do índice desejado: "))

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

if codigo_indice in indices:
    indice = indices[codigo_indice]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")
    exit()

# Diretório onde os arquivos .csv estão armazenados
data_dir = r"C:/Users/armen/OneDrive/Estratégias/Base/Diária"

# Obtém a lista de ativos a partir do arquivo mais recente na pasta da lista do índice selecionado
lista_dir = f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*"
list_of_files = glob.glob(lista_dir)
if not list_of_files:
    print(f"Nenhum arquivo encontrado em: {lista_dir}")
    exit()

latest_file = max(list_of_files, key=os.path.getctime)

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

# -------------------------------
# Leitura do Benchmark (Ibovespa)
# -------------------------------
benchmark_file = os.path.join(data_dir, "IBOV_B_0_Diário.csv")
if not os.path.exists(benchmark_file):
    print("Arquivo do IBOV não encontrado!")
    exit()

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

# -------------------------------
# Processamento de Cada Ativo
# -------------------------------
results = []       # Lista para armazenar os resultados
rolling_window = 30  # Tamanho da janela para o cálculo do rolling slope
smoothing_span = 3   # Parâmetro para suavização (ajuste conforme necessário)

for codigo_acao in ativos:
    codigo_acao = str(codigo_acao).strip()
    asset_file = os.path.join(data_dir, f"{codigo_acao}_B_0_Diário.csv")
    if not os.path.exists(asset_file):
        print(f"Arquivo da ação {codigo_acao} não encontrado, pulando...")
        continue

    # Leitura do arquivo da ação
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

    # Realiza o merge com os dados do benchmark (Ibovespa) com base na Data
    merged = pd.merge(dados, ibov[["Data", "Fechamento"]], on="Data", how="inner")
    merged.rename(columns={"Fechamento": "Indice"}, inplace=True)
    if merged.empty:
        print(f"Dados vazios para a ação {codigo_acao} após merge com o benchmark, pulando...")
        continue

    # -------------------------------
    # Cálculo das Funções Reais do RRG
    # -------------------------------
    merged["RS"] = merged["Ação"] / merged["Indice"]
    merged["logRS"] = np.log(merged["RS"])
    merged["slope"] = merged["logRS"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
    merged["theta"] = np.degrees(np.arctan(merged["slope"]))
    merged["rotation"] = merged["theta"].diff()

    merged_clean = merged.dropna(subset=["theta", "rotation"]).reset_index(drop=True)
    dados_last10 = merged_clean.tail(10)
    if len(dados_last10) < 2:
        print(f"Dados insuficientes para {codigo_acao} (menos de 10 dias), pulando...")
        continue

    # -------------------------------
    # Suavização da "Calda" (últimos 10 dias)
    # -------------------------------
    smoothed_theta = dados_last10["theta"].ewm(span=smoothing_span, adjust=False).mean()
    smoothed_rotation = dados_last10["rotation"].ewm(span=smoothing_span, adjust=False).mean()

    # Utiliza os valores suavizados para definir os valores finais
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
    # Cálculo da Direção (usando os dois últimos pontos suavizados)
    # -------------------------------
    dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
    dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
    angle_movement = math.degrees(math.atan2(dy, dx))
    direcao = get_cardinal_direction(angle_movement)

    # Armazena o resultado para o ativo
    results.append({
        "Ação": codigo_acao,
        "Quadrante": quadrante,
        "Direção": direcao,
        "Theta (graus)": round(theta_final, 2),
        "Rotação (graus)": round(rotation_final, 2)
    })
    print(f"Processado {codigo_acao}: Quadrante = {quadrante}, Direção = {direcao}")

# -------------------------------
# Geração do Arquivo Excel com os Resultados
# -------------------------------
if results:
    df_resultados = pd.DataFrame(results)
    output_excel = "ativos_quadrante_direcao.xlsx"
    df_resultados.to_excel(output_excel, index=False)
    print(f"\nArquivo Excel '{output_excel}' criado com sucesso!")
else:
    print("Nenhum resultado foi processado.")
