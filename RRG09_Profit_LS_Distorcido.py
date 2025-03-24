import os
import math
import glob
import itertools
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def rolling_slope(x):
    t = np.arange(len(x))
    slope, _ = np.polyfit(t, x, 1)
    return slope


def get_cardinal_direction(angle):
    if 22.5 < angle <= 67.5:
        return "Nordeste"
    elif -67.5 < angle <= -22.5:
        return "Sudeste"
    elif 67.5 < angle <= 112.5:
        return "Norte"
    elif -112.5 < angle <= -67.5:
        return "Sul"
    return "Indeterminado"


print("Escolha um índice:")
indices = {1: "IBOV", 2: "IBRA", 3: "BDRX", 4: "ICON", 5: "IDIV", 6: "IEEX",
           7: "IFIX", 8: "IFNC", 9: "IMAT", 10: "IMOB", 11: "INDX", 12: "MLCX",
           13: "SMLL", 14: "UTIL", 15: "OIL"}

for k, v in indices.items():
    print(f"{k} - {v}")

codigo_indice = int(input("Digite o número do índice desejado: "))
if codigo_indice not in indices:
    print("Código de índice inválido.")
    exit()

indice = indices[codigo_indice]
print(f"Você selecionou o índice {indice}.")

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
ativos = lista["Código"].dropna().str.strip().tolist()

ativos_combinados = list(itertools.combinations(ativos, 2))

benchmark_file = os.path.join(data_dir, "IBOV_B_0_Diário.csv")
if not os.path.exists(benchmark_file):
    print("Arquivo do IBOV não encontrado!")
    exit()

ibov = pd.read_csv(benchmark_file, sep=";", encoding="ISO-8859-1", skiprows=0,
                   skipfooter=2, engine="python", thousands=".", decimal=",",
                   header=0)
ibov["Data"] = pd.to_datetime(ibov["Data"], format="%d/%m/%Y")
ibov = ibov.sort_values(by="Data", ascending=True)
ibov = ibov.rename({"Fechamento": "IBOV"}, axis=1)


results = []
rolling_window = 21
smoothing_span = 9
moving_avg_window = 252

for ativo1, ativo2 in ativos_combinados:
    file1 = os.path.join(data_dir, f"{ativo1}_B_0_Diário.csv")
    file2 = os.path.join(data_dir, f"{ativo2}_B_0_Diário.csv")
    if not os.path.exists(file1) or not os.path.exists(file2):
        continue

    df1 = pd.read_csv(file1, sep=";", encoding="ISO-8859-1", skiprows=0, skipfooter=2,
                      engine="python", thousands=".", decimal=",", header=0)
    df2 = pd.read_csv(file2, sep=";", encoding="ISO-8859-1", skiprows=0, skipfooter=2,
                      engine="python", thousands=".", decimal=",", header=0)
    df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")
    df1 = df1.sort_values(by="Data", ascending=True)
    df2["Data"] = pd.to_datetime(df2["Data"], format="%d/%m/%Y")
    df2 = df2.sort_values(by="Data", ascending=True)

    merged1 = pd.merge(df1, df2, on="Data", how="inner", suffixes=("_1", "_2"))
    merged = pd.merge(merged1, ibov[["Data", "IBOV"]], on="Data", how="inner")
    if merged.empty:
        continue

    merged["Ratio"] = merged["Fechamento_1"] / merged["Fechamento_2"]
    merged["Ratio_MA"] = merged["Ratio"].rolling(window=moving_avg_window).mean()
    merged["Ratio_STD"] = merged["Ratio"].rolling(window=moving_avg_window).std()
    merged["Lower_Band"] = merged["Ratio_MA"] - 2 * merged["Ratio_STD"]

    if merged["Ratio"].iloc[-2] <= merged["Lower_Band"].iloc[-2] and merged["Ratio"].iloc[-1] >= merged["Lower_Band"].iloc[-1]:
        merged["logRatio"] = np.log(merged["Ratio"]/merged["IBOV"])
        merged["slope"] = merged["logRatio"].rolling(window=rolling_window).apply(rolling_slope, raw=True)
        merged["theta"] = np.degrees(np.arctan(merged["slope"]))
        merged["rotation"] = merged["theta"].diff()
        merged.dropna(subset=["theta", "rotation"], inplace=True)

        smoothed_theta = merged["theta"].ewm(span=smoothing_span, adjust=False).mean()
        smoothed_rotation = merged["rotation"].ewm(span=smoothing_span, adjust=False).mean()

        theta_final = smoothed_theta.iloc[-1]
        rotation_final = smoothed_rotation.iloc[-1]

        quadrante = "FORTALECENDO" if theta_final < 0 and rotation_final > 0 else "FORTE" if theta_final > 0 and rotation_final > 0 else "Indeterminado"

        dx = smoothed_theta.iloc[-1] - smoothed_theta.iloc[-2]
        dy = smoothed_rotation.iloc[-1] - smoothed_rotation.iloc[-2]
        angle_movement = math.degrees(math.atan2(dy, dx))
        direcao = get_cardinal_direction(angle_movement)

        if quadrante in ["FORTALECENDO", "FORTE"] and direcao == "Nordeste":
            results.append({"Long": f"{ativo1}", "Short": f"{ativo2}", "Quadrante": quadrante,
                            "Direção": direcao, "Theta": round(theta_final, 2),
                            "Rotação": round(rotation_final, 2)})

if results:
    df_resultados = pd.DataFrame(results)
    output_excel = f"RRG_Ratio_Distorcido_{indice}.xlsx"
    df_resultados.to_excel(output_excel, index=False)
    print(f"Arquivo Excel '{output_excel}' criado com sucesso!")
else:
    print("Nenhum resultado foi processado.")
