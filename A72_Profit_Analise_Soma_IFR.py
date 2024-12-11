import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import os
import pandas as pd
import numpy as np
import datetime

def n_ampl_index_cp(alta, baixa):
    # Calcula o n_ampl Index
    n_ampl_cp = alta - baixa

    return n_ampl_cp


def n_ampl_index_lp(alta, baixa):
    # Calcula o n_ampl Index
    n_ampl_lp = alta - baixa

    return n_ampl_lp



#Permite que o usuário escolha entre o IBOV, IBRA, BDRX, ICON, IDIV, IEEX, IFIX, IFNC, IMAT, IMOB, INDX, MLCX, SMLL, UTIL

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
codigo = int(input("Digite o número do índice desejado: "))

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

# Verifica se o código digitado pelo usuário está no dicionário
if codigo in indices:
    indice = indices[codigo]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")

# Agora, a variável "indice" contém o código selecionado (ou é None se o código for inválido)


# Local onde está o arquivo CSV que contém a lista de ações do índice selecionado
list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*"
)  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)
#Carrega o arquivo CSV
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


df = pd.DataFrame(lista)
#Cria uma variável que contém apenas o Código das ações
acoes = df["Código"]
data_atual = datetime.date.today()
dt = data_atual.strftime("%d/%m/%Y")
print(len(acoes), "ações")
print("##################################")
print("")
print(f"Análise de Amplitude do ${indice} - {dt}")
print("")






# Diretório onde os arquivos CSV com as séries históricas das ações estão localizados
diretorio = "C:/Users/armen/OneDrive/Estratégias/Base/Diária/"


# Criar um DataFrame vazio para armazenar os resultados
resultados = pd.DataFrame()
dfs_temp = []
RSI_resultados = []

# Cria listas vazias para armazenar as tendências de alta e baixa no curto e médio prazo para cada dia
dfs_alta_cp = []
dfs_baixa_cp = []
dfs_alta_cp_lp = []
dfs_baixa_lp = []
# Cria listas vazias para armazenar os avanços e declínios de cada dia
dfs_advances = []
dfs_declines = []
dfs_vol_adv = []
dfs_vol_dec = []


for acao in acoes:
    arquivo = os.path.join(diretorio, f"{acao}_B_0_Diário.csv")

    # Carregar o arquivo CSV da ação
    df = pd.read_csv(
        arquivo,
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

    # Defina a data como índice e ordene o DataFrame por data
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
    df = df.sort_values(by=["Data"], ascending=True)
    df.set_index("Data", inplace=True)

    # Calcular as novas altas e baixas nos últimos 252 dias
    df["Nova_Alta"] = df["Fechamento"].rolling(252).max()
    df["Nova_Baixa"] = df["Fechamento"].rolling(252).min()

    # Remover os NaN resultantes do cálculo
    df = df.dropna()

    # Verificar se a ação fez nova máxima e nova mínima em relação aos últimos 252 dias
    df["Fez_Nova_Alta"] = df["Fechamento"] == df["Nova_Alta"]
    df["Fez_Nova_Baixa"] = df["Fechamento"] == df["Nova_Baixa"]

    # Adicionar os resultados ao DataFrame de resultados
    novo_frame = df[["Fez_Nova_Alta", "Fez_Nova_Baixa"]].astype(int)
    resultados = resultados.copy()
    resultados = pd.concat([resultados, novo_frame], axis=1)
    resultados.columns = resultados.columns.str.replace(
        "Fez_Nova_Alta", acao + "_Nova_Alta"
    )
    resultados.columns = resultados.columns.str.replace(
        "Fez_Nova_Baixa", acao + "_Nova_Baixa"
    )

    # Calcular a Linha de Avaço e Declínio do SP500
    df1 = pd.DataFrame(df)

    condition_1 = df1["Fechamento"].diff()

    df1["signal"] = condition_1 > 0

    # Armazenar o DataFrame temporário na lista
    dfs_temp.append(df1["signal"].astype(int))

    # Calcular somatória de sobrecomprados e sobrevendidos
    df2 = pd.DataFrame(df)
    df2["RSI"] = talib.RSI(df2["Fechamento"], timeperiod=14)
    df2["RSI_gt_70"] = df2["RSI"] > 70
    df2["RSI_lw_30"] = df2["RSI"] < 30
    RSI_resultados.append(df2[["RSI_gt_70", "RSI_lw_30"]])

    mme9 = df1["Fechamento"].ewm(span=9, adjust=True).mean()
    mme21 = df1["Fechamento"].ewm(span=21, adjust=True).mean()
    mme50 = df1["Fechamento"].ewm(span=50, adjust=True).mean()
    mme200 = df1["Fechamento"].ewm(span=200, adjust=True).mean()
    fech = df1["Fechamento"]

    df["Alta"] = (fech > mme9) & (mme9 > mme21)
    df["Baixa"] = (fech < mme9) & (mme9 < mme21)
    df["Alta_lp"] = (fech > mme50) & (mme50 > mme200)
    df["Baixa_lp"] = (fech < mme50) & (mme50 < mme200)

    # Armazenar o DataFrame temporário na lista
    dfs_alta_cp.append(df["Alta"].astype(int))
    dfs_baixa_cp.append(df["Baixa"].astype(int))
    dfs_alta_cp_lp.append(df["Alta_lp"].astype(int))
    dfs_baixa_lp.append(df["Baixa_lp"].astype(int))


    condition_1 = df1["Fechamento"].diff()

    df1["Avanço"] = condition_1 > 0
    df1["Declinio"] = condition_1 < 0

    # Armazenar o DataFrame temporário na lista
    dfs_advances.append(df1["Avanço"].astype(int))
    dfs_declines.append(df1["Declinio"].astype(int))

    # Adicionar volumes às listas para as linhas em que "Avanço" é verdadeiro
    if df1["Avanço"].any():
        dfs_vol_adv.append(df1.loc[df1["Avanço"], "Volume"])

    # Adicionar volumes/Dk listas para as linhas em que "Declinio" é verdadeiro
    if df1["Declinio"].any():
        dfs_vol_dec.append(df1.loc[df1["Declinio"], "Volume"])


# Calcular o número total de ações que fizeram nova alta e nova baixa em cada dia
resultados["Total_Nova_Alta"] = resultados.filter(like="_Nova_Alta").sum(axis=1)
resultados["Total_Nova_Baixa"] = resultados.filter(like="_Nova_Baixa").sum(axis=1)
resultados["NH_NL_I"] = (resultados["Total_Nova_Alta"] - resultados["Total_Nova_Baixa"])

resultados.fillna({"NH_NL_I": 0}, inplace=True)
resultados["NH_NL_I_Media_Movel_10"] = resultados["NH_NL_I"].rolling(window=10).mean()


# Calcular a média móvel dos últimos 20 dias de resultados['NH_NL_I']
resultados["NH_NL_I_Media_Movel"] = (
    resultados["NH_NL_I_Media_Movel_10"].rolling(window=10).mean()
)
resultados.fillna({"NH_NL_I_Media_Movel_10": 0}, inplace=True)
resultados.fillna({"NH_NL_I_Media_Movel": 0}, inplace=True)


############

#Cria a columa Cruzamento para identificar a tendência de alta ou baixa
resultados["Cruzamento"] = 0
#Cria a columa Mudança para identificar quando a tendência de alta ou baixa mudou
resultados["Mudança"] = 0
#Cria a coluna Distancia Inicial para calcular a distância incial entre o indicador e a sua média movel no momento da
#mudança de tendência
resultados["Distancia Inicial"] = 0
#Cria a coluna Distancia Atual para calcular a distância final entre o indicador e a sua média movel
resultados["Distancia Atual"] = 0
#Cria a coluna Distancimento para calcular a diferença entre a distância inicial e a distância atual
resultados["Distancimento"] = 0
#Cria a coluna Analise Dist para vericar se o indicador está se aproximando ou afastando da sua medida movel
resultados["Analise Dist"] = 0

resultados.reset_index(inplace=True)



# Faz a análise de cada linha para identificar a tendência
for index, row in resultados.iterrows():
    if row["NH_NL_I_Media_Movel_10"] > row["NH_NL_I_Media_Movel"]:
        resultados.loc[index,"Cruzamento"] = 1
    elif row["NH_NL_I_Media_Movel_10"] < row["NH_NL_I_Media_Movel"]:
        resultados.loc[index, "Cruzamento"] = -1
    else:
        resultados.loc[index, "Cruzamento"] = 0

# Faz a análise de cada linha para identificar quando a tendência de alta ou baixa mudou
for index, row in resultados.iterrows():
    if isinstance(index, int) and index > 0 and row["Cruzamento"] != resultados.iloc[index-1]["Cruzamento"]:
        resultados.loc[index, "Mudança"] = 1
    else:
        resultados.loc[index, "Mudança"] = 0


#Faz um loop para calcular a distância inicial entre o indicador e a sua média a partir da mudança de tendência
for index in range(1,len(resultados)):
    if resultados.loc[index, "Mudança"] == 1 and resultados.loc[index, "Cruzamento"] == 1:
        resultados.loc[index, "Distancia Inicial"] = abs(resultados.loc[index, "NH_NL_I_Media_Movel_10"] - resultados.loc[index, "NH_NL_I_Media_Movel"])
    elif resultados.loc[index, "Mudança"] != 1 and resultados.loc[index, "Cruzamento"] == 1:
        resultados.loc[index, "Distancia Inicial"] = resultados.loc[index-1,"Distancia Inicial"]
    elif resultados.loc[index,"Mudança"] == 1 and resultados.loc[index, "Cruzamento"] == -1:
        resultados.loc[index,"Distancia Inicial"] = abs(resultados.loc[index, "NH_NL_I_Media_Movel_10"] - resultados.loc[index, "NH_NL_I_Media_Movel"])
    elif resultados.loc[index, "Mudança"] != 1 and resultados.loc[index, "Cruzamento"] == -1:
        resultados.loc[index, "Distancia Inicial"] = resultados.loc[index-1,"Distancia Inicial"]
    else:
        resultados.loc[index,"Distancia Inicial"]= 0

#Faz um loop para calcular a distância atual entre o indicador e a sua média
for i in range(len(resultados)):
    resultados.loc[i,"Distancia Atual"] = abs(resultados.loc[i,"NH_NL_I_Media_Movel_10"] - resultados.loc[i,"NH_NL_I_Media_Movel"])

#Faz um loop para calcular a diferença entre a distância inicial e a distância atual
for i in range(len(resultados)):
    resultados.loc[i,"Distancimento"]= resultados.loc[i,"Distancia Atual"] - resultados.loc[i, "Distancia Inicial"]

#Faz um loop para ver se o indicador está se aproximando ou afastando da sua medida movel
for i in range(1,len(resultados)):
    if resultados.loc[i,"Distancimento"] > resultados.loc[i-1,"Distancimento"]:
        resultados.loc[i,"Analise Dist"] = 1
    elif resultados.loc[i,"Distancimento"] < resultados.loc[i-1,"Distancimento"]:
        resultados.loc[i,"Analise Dist"]= -1
    else:
        resultados.loc[i,"Analise Dist"] = 0

mhnli_d_mais_0 = resultados.loc[resultados.index[-1],"Analise Dist"]
nhnli_d_menos_1 = resultados.loc[resultados.index[-2],"Analise Dist"]
nhnli_d_menos_2 = resultados.loc[resultados.index[-3],"Analise Dist"]
nhnli_d_menos_3 = resultados.loc[resultados.index[-4],"Analise Dist"]

print("Distanciamento da média Movel")
print("NH NL I:", nhnli_d_menos_3, nhnli_d_menos_2, nhnli_d_menos_1, mhnli_d_mais_0)


##################################
# Concatenar os DataFrames temporários para criar df3
df3 = pd.concat(dfs_temp, axis=1)

# Substituir 0 por -1 em todo o DataFrame
df3.replace(0, -1, inplace=True)

# Calcular a coluna "Soma" usando a vetorização
df3["Soma"] = df3.sum(axis=1)

# Calcular a coluna "addc", LAD
df3["addc1"] = df3["Soma"].cumsum()

df3["addc"] = df3["addc1"].ewm(span=7, adjust=True).mean()

# Calcular a média móvel de addc, LAD
df3["addc_MMA"] = df3["addc"].rolling(window=21).mean()


# Concatenar os resultados de todos os ativos do RSI_resultados
merged_df = pd.concat(RSI_resultados)

merged_df = merged_df.groupby(merged_df.index).sum()


# Concatenar os DataFrames temporários para criar dfs_high
dfs_high = pd.concat(dfs_alta_cp, axis=1)
dfs_high_lp = pd.concat(dfs_alta_cp_lp, axis=1)

# Calcular a coluna "Soma" usando a vetorização
dfs_high["Soma"] = dfs_high.sum(axis=1)
dfs_high_lp["Soma"] = dfs_high_lp.sum(axis=1)

# Concatenar os DataFrames temporários para criar dfs_dowm
dfs_dowm = pd.concat(dfs_baixa_cp, axis=1)
dfs_dowm_lp = pd.concat(dfs_baixa_lp, axis=1)


# Calcular a coluna "Soma" usando a vetorização
dfs_dowm["Soma"] = dfs_dowm.sum(axis=1)
dfs_dowm_lp["Soma"] = dfs_dowm_lp.sum(axis=1)


data1 = pd.DataFrame()


data1["High"] = dfs_high["Soma"]
data1["Down"] = dfs_dowm["Soma"]
data1["High_lp"] = dfs_high_lp["Soma"]
data1["Down_lp"] = dfs_dowm_lp["Soma"]

df4 = pd.DataFrame(data1)

n_ampl_cp = n_ampl_index_cp(df4["High"], df4["Down"])

n_ampl_cp = pd.DataFrame(n_ampl_cp)

n_ampl_lp = n_ampl_index_lp(df4["High_lp"], df4["Down_lp"])

n_ampl_lp = pd.DataFrame(n_ampl_lp)

# Adiciona as colunas ao DataFrame original com nomes específicos
n_ampl = pd.concat([n_ampl_cp, n_ampl_lp], axis=1)
n_ampl.columns = ["Nova Amplitude CP", "Nova Amplitude LP"]
n_ampl = pd.DataFrame(n_ampl)
n_ampl_180 = n_ampl.iloc[-200:]


# Concatenar os DataFrames temporários para criar df_av
df_av = pd.concat(dfs_advances, axis=1)

# Calcular a coluna "Soma" usando a vetorização
df_av["Soma"] = df_av.sum(axis=1)


# Concatenar os DataFrames temporários para criar df_dec
df_dec = pd.concat(dfs_declines, axis=1)

# Calcular a coluna "Soma" usando a vetorização
df_dec["Soma"] = df_dec.sum(axis=1)


df_vol_adv = pd.concat(dfs_vol_adv, axis=1)

df_vol_adv["Soma"] = df_vol_adv.sum(axis=1)

df_vol_dec = pd.concat(dfs_vol_dec, axis=1)

df_vol_dec["Soma"] = df_vol_dec.sum(axis=1)


data = pd.DataFrame()


data["Advances"] = df_av["Soma"]
data["Declines"] = df_dec["Soma"]
data["Volume Advances"] = df_vol_adv["Soma"]
data["Volume Declines"] = df_vol_dec["Soma"]





# Monta a série do índice selecionado
ind = pd.read_csv(
    f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{indice}_B_0_Diário.csv",
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
ind = pd.DataFrame(ind)
ind["Data"] = pd.to_datetime(ind["Data"], format="%d/%m/%Y")
ind.drop(
    columns=["Ativo", "Abertura", "Máximo", "Mínimo", "Volume", "Quantidade"],
    inplace=True,
)
ind = ind.sort_values(by=["Data"], ascending=True)
ind.set_index("Data", inplace=True)


# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
resultados_250 = resultados.iloc[-200:]


# Calcular a derivada de y em relação a x
dNHNL_dx = np.gradient(resultados_250["NH_NL_I_Media_Movel_10"],resultados_250.index)

# Verificar direção da curva
direction_NHNL = np.sign(dNHNL_dx)
print("NHNL",direction_NHNL[-5:])

dNHNLmm_dx = np.gradient(resultados_250["NH_NL_I_Media_Movel"],resultados_250.index)
direction_NHNLmm = np.sign(dNHNLmm_dx)
print("NHNLmm",direction_NHNLmm[-5:])



# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
df3_250 = df3.iloc[-200:]

# Ajuste o DataFrame merged_df para incluir apenas os últimos 200 dias
merged_df_250 = merged_df.iloc[-200:]

# Ajuste o DataFrame SP500_df para incluir apenas os últimos 200 dias
ind_250 = ind.iloc[-200:]


# Crie subplots com três linhas (uma para cada gráfico)

# Crie subplots
fig = make_subplots(rows=2, cols=1, shared_xaxes=True)


# Adicione o gráfico do somatório de sobrecomprados e sobrevendidos na primeira linha
fig.add_trace(
    go.Scatter(
        x=merged_df_250.index,
        y=merged_df_250["RSI_gt_70"],
        mode="lines",
        name="IFR > 70",
        line=dict(color="blue"),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=merged_df_250.index,
        y=merged_df_250["RSI_lw_30"],
        mode="lines",
        name="IFR < 30",
        line=dict(color="red"),
    ),
    row=1,
    col=1,
)


# # Adicione o gráfico de linha do índice na segunda linha
fig.add_trace(
    go.Scatter(
        x=ind_250.index,
        y=ind_250["Fechamento"],
        mode="lines",
        name=f"{indice}",
        line=dict(color='#063970')  # Substitua 'cor_desejada' pela cor desejada
    ),
    row=2,
    col=1,
)
# Adicione as anotações de fonte aos subplots
fig.add_annotation(
    text="",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=16, color="gray"),
)


# Atualize os layouts dos subplots
fig.update_layout(
    title_text=f"Somatório dos IFRs - {indice} - {dt}",
    showlegend=True,
    xaxis_rangeslider_visible=False,
    title_font=dict(size=24)
)

fig.update_xaxes(
    tickfont=dict(size=18),  # Ajuste o tamanho para o desejado
    row=2, col=1  # Aplique à linha e coluna específicas
)

fig.update_yaxes(title_text="Somatório dos IFRs", row=1, col=1,title_font=dict(size=20))
fig.update_yaxes(title_text=f"{indice}", row=2, col=1, title_font=dict(size=20))
fig.update_xaxes(title_text="Data", row=2, col=1, title_font=dict(size=20))

fig.update_legends(font=dict(size=18))
fig.update_annotations(
    dict(
        xref="paper",
        yref="paper",
        x=0,
        y=-0.1,
    )
)
# Exiba os subplots
fig.show()



