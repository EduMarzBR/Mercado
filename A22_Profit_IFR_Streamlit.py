import glob
import os
import pandas as pd
import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime

#streamlit run C:\Users\armen\PycharmProjects\Profit\A22_Profit_IFR_Streamlit.py

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



list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*"
)  # * means all if need specific format then *.csv
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


df = pd.DataFrame(lista)
acoes = df["Código"]


# Diretório onde os arquivos CSV estão localizados
diretorio = "C:/Users/armen/OneDrive/Estratégias/Base/Diária/"


# Criar um DataFrame vazio para armazenar os resultados
resultados = pd.DataFrame()


# Calcular a Linha de Avaço e Declínio e de Somatória do IFR IBRA
IFR_resultados = []
IFR_Sobrecompradados = []
IFR_Sobrevendidos = []
for x in acoes:
    acn = pd.read_csv(
        "C:/Users/armen/OneDrive/Estratégias/Base/Diária/" + x + "_B_0_Diário.csv",
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
    df1 = pd.DataFrame(acn)
    df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")

    df1 = df1.sort_values(by=["Data"], ascending=True)
    df1["IFR"] = talib.RSI(df1["Fechamento"], timeperiod=14)
    df1["Sobrecomprada"] = (df1["IFR"] > 70) 
    df1["Sobrevendida"] = (df1["IFR"] < 30)
    pd.set_option('future.no_silent_downcasting', True)
    df1.replace(True, 1, inplace=True)
    df1.replace(False, 0, inplace=True)

    IFR_resultados.append(df1[["Data", "Sobrecomprada", "Sobrevendida"]])

    try:
        if df1["Sobrecomprada"].iloc[-1] == 1:
            IFR_Sobrecompradados.append(f"{x}")
        if df1["Sobrevendida"].iloc[-1] == 1:
            IFR_Sobrevendidos.append(f"{x}")
    except:
        pass


# Concatenar os resultados de todos os ativos



merged_df = pd.concat(IFR_resultados)
merged_df["Data"] = pd.to_datetime(merged_df["Data"], format="%d/%m/%Y")

merged_df = merged_df.sort_values(by=["Data"], ascending=True)
merged_df.set_index("Data", inplace=True)
merged_df = merged_df.groupby(merged_df.index).sum()


# Monta a série do IBRA
IBRA = pd.read_csv(
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
IBRA = pd.DataFrame(IBRA)
IBRA["Data"] = pd.to_datetime(IBRA["Data"], format="%d/%m/%Y")
IBRA.drop(
    columns=["Ativo", "Abertura", "Máximo", "Mínimo", "Volume", "Quantidade"],
    inplace=True,
)
IBRA = IBRA.sort_values(by=["Data"], ascending=True)
IBRA.set_index("Data", inplace=True)


# Ajuste o DataFrame RSI_resultados para incluir apenas os últimos 200 dias
merged_df_250 = merged_df.iloc[-200:]

# Ajuste o DataFrame IBRA_df para incluir apenas os últimos 200 dias
IBRA_250 = IBRA.iloc[-200:]

# Traz a data atual

data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")

# Crie subplots com três linhas (uma para cada gráfico)

# Ajuste do tamanho dos gráficos
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])

# Adicionar traces aos subplots
fig.add_trace(
    go.Scatter(x=merged_df_250.index, y=merged_df_250['Sobrecomprada'], mode='lines', name='Sobrecompradas', line=dict(color='#87CEEB')),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=merged_df_250.index, y=merged_df_250['Sobrevendida'], mode='lines', name='Sobrevendidas', line=dict(color='red')),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=IBRA_250.index, y=IBRA_250['Fechamento'], mode='lines', name='IBRA'),
    row=2, col=1
)

# Atualizar layout
fig.update_layout(
    title_text=f"Ações do {indice} Sobrecompradadas e Sobrevendidas pelo IFR vs. {indice} - {dt}",
    title_font=dict(size=20),
    legend=dict(font=dict(size=19))  # Para ocultar a legenda duplicada
)
#fig.update_layout()
fig.update_yaxes(title_text="Ações", row=1, col=1, title_font=dict(size=18))
fig.update_yaxes(title_text=f"{indice}", row=2, col=1, title_font=dict(size=18))
fig.update_xaxes(title_text="Data", row=2, col=1, title_font=dict(size=18))

# Adicionar anotação
fig.add_annotation(
    text="Fonte: Nelogica e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=18, color="gray"),
)

# Exibir o gráfico usando Streamlit
st.plotly_chart(fig)


print("")
print(f"**Ações do ${indice} Sobrecompradas e Sobrevendidas pelo IFR- {dt}**")
print("")
print("Interpretação do gráfico: Quando a linha das ações sobrecompradas supera a linha das ações sobrevendidas, "
      "aumentam as chances de entrada do índice em tendência de alta. Quando ocorre o inverso, aumentam as chances de "
      "o índice entrar em tendência de baixa.")
print("")
print(f"Ações Sobrecompradas pelo IFR ({len(IFR_Sobrecompradados)} ativos): {IFR_Sobrecompradados}")
print("")
print(f"Ações Sobrevendidas pelo IFR ({len(IFR_Sobrevendidos)} ativos): {IFR_Sobrevendidos}")
print("")
print("Sobrecompradas: são as ações cuja medida do IFR está acima de 70")
print("")
print("Sobrevendidas: são as ações cuja medida do IFR está abaixo de 30")
print("")
print("O que é o IFR?")
print("")
print("O Índice de Força Relativa (IFR), ou Relative Strength Index (RSI) em inglês, é um indicador de análise "
      "técnica que ajuda os traders e investidores a avaliarem a força e a direção potencial de uma tendência em um "
      "ativo financeiro. Ele foi desenvolvido por J. Welles Wilder e é amplamente utilizado para identificar "
      "condições de sobrecompra e sobrevenda em um mercado.")