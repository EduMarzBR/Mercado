import glob
import os
import pandas as pd
import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

indices = ["IBRA","IBOV","SMLL","ICON","MLCX","IDIV","INDX","UTIL","IMOB","IFNC","IEEX","IMAT"]
df4 = pd.DataFrame()
for ind in indices:
    list_of_files = glob.glob(f"C:/Users/armen/OneDrive/Estratégias/Listas/{ind}/*") # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    lista = pd.read_csv(latest_file, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python',
                            thousands='.', decimal=',', header=1, index_col=False)


    df = pd.DataFrame(lista)
    acoes = df['Código']


    # Diretório onde os arquivos CSV estão localizados
    diretorio = "C:/Users/armen/OneDrive/Estratégias/Base/Diária/"


    # Calcular a Linha de Avaço e Declínio
    dfs_temp = []

    for x in acoes:
        acn = pd.read_csv("C:/Users/armen/OneDrive/Estratégias/Base/Diária/" + x + "_B_0_Diário.csv", sep=';',
        encoding='ISO-8859-1', skiprows=0, skipfooter=0, engine='python', thousands='.', decimal=',',
        header=0, index_col=False)
        df1 = pd.DataFrame(acn)
        df1['Data'] = pd.to_datetime(df1['Data'], format="%d/%m/%Y")

        df1 = df1.sort_values(by=['Data'], ascending=True)
        df1.set_index('Data', inplace=True)
        condition_1 = df1["Fechamento"].diff()

        df1[f"signal"] = condition_1 > 0

        # Armazenar o DataFrame temporário na lista
        dfs_temp.append(df1[f"signal"].astype(int))



        # Concatenar os DataFrames temporários para criar df3
        df3 = pd.concat(dfs_temp, axis=1)

        # Substituir 0 por -1 em todo o DataFrame
        df3.replace(0, -1, inplace=True)



        # Calcular a coluna "Soma" usando a vetorização
        df4[f"Soma {ind}"] = df3.sum(axis=1)

        # Calcular a coluna "addc" e sua média móvel
        mma=30
        df4[f"addc {ind}"] = df4[f"Soma {ind}"].cumsum()
        df4[f'LAD MMA {ind}'] = df4[f'addc {ind}'].rolling(window=mma).mean()


# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
df4_250 = df4.iloc[-100:]






#Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")

# Crie subplots com três linhas (uma para cada gráfico)

fig = make_subplots(rows=6, cols=2, shared_xaxes=True)



# # Adicione o gráfico de linha da LAD IBRA
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IBRA'], mode='lines', name='LAD IBRA', line=dict(color='blue')), row=1, col=1)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IBRA'], mode='lines', name=f'MMA{mma} IBRA',line=dict(color='red')), row=1, col=1)
# # Adicione o gráfico de linha da LAD IBOV
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IBOV'], mode='lines', name='LAD IBOV', line=dict(color='blue')), row=1, col=2)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IBOV'], mode='lines', name=f'MMA{mma} IBOV', line=dict(color='red')), row=1, col=2)
# # Adicione o gráfico de linha da LAD SMLL
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc SMLL'], mode='lines', name='LAD SMLL', line=dict(color='blue')), row=2, col=1)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA SMLL'], mode='lines', name=f'MMA{mma} SMLL', line=dict(color='red')), row=2, col=1)
# # Adicione o gráfico de linha da LAD ICON
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc ICON'], mode='lines', name='LAD ICON', line=dict(color='blue')), row=2, col=2)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA ICON'], mode='lines', name=f'MMA{mma} ICON', line=dict(color='red')), row=2, col=2)
# # Adicione o gráfico de linha da LAD MLCX
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc MLCX'], mode='lines', name='LAD MLCX', line=dict(color='blue')), row=3, col=1)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA MLCX'], mode='lines', name=f'MMA{mma} MLCX', line=dict(color='red')), row=3, col=1)
# # Adicione o gráfico de linha da LAD IDIV
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IDIV'], mode='lines', name='LAD IDIV', line=dict(color='blue')), row=3, col=2)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IDIV'], mode='lines', name=f'MMA{mma} IDIV', line=dict(color='red')), row=3, col=2)
# # Adicione o gráfico de linha da LAD INDX
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc INDX'], mode='lines', name='LAD INDX', line=dict(color='blue')), row=4, col=1)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA INDX'], mode='lines', name=f'MMA{mma} INDX', line=dict(color='red')), row=4, col=1)
# # Adicione o gráfico de linha da LAD UTIL
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc UTIL'], mode='lines', name='LAD UTIL', line=dict(color='blue')), row=4, col=2)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA UTIL'], mode='lines', name=f'MMA{mma} UTIL', line=dict(color='red')), row=4, col=2)
# # Adicione o gráfico de linha da LAD IMOB
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IMOB'], mode='lines', name='LAD IMOB', line=dict(color='blue')), row=5, col=1)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IMOB'], mode='lines', name=f'MMA{mma} IMOB', line=dict(color='red')), row=5, col=1)
# # Adicione o gráfico de linha da LAD IFNC
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IFNC'], mode='lines', name='LAD IFNC', line=dict(color='blue')), row=5, col=2)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IFNC'], mode='lines', name=f'MMA{mma} IFNC', line=dict(color='red')), row=5, col=2)
# # Adicione o gráfico de linha da LAD IEEX
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IEEX'], mode='lines', name='LAD IEEX', line=dict(color='blue')), row=6, col=1)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IEEX'], mode='lines', name=f'MMA{mma} IEEX', line=dict(color='red')), row=6, col=1)
# # Adicione o gráfico de linha da LAD IMAT
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['addc IMAT'], mode='lines', name='LAD IMAT', line=dict(color='blue')), row=6, col=2)
fig.add_trace(go.Scatter(x=df4_250.index, y=df4_250['LAD MMA IMAT'], mode='lines', name=f'MMA{mma} IMAT', line=dict(color='red')), row=6, col=2)




fig.add_annotation(
    text="Fonte: Nelogica e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper", yref="paper",
    x=0, y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray")
)


# Atualize as cores 'cor1' e 'cor2' com as cores desejadas, por exemplo, 'blue' e 'red'
fig.update_traces(marker=dict(size=10))
# Atualize os layouts dos subplots
fig.update_layout(title_text=f"Linhas de Avanço e Declínio - {dt}", title_font=dict(size=20))
fig.update_yaxes(title_text="IBRA", row=1, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="IBOV", row=1, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="SMLL", row=2, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="ICON", row=2, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="MLCX", row=3, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="IDIV", row=3, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="INDX", row=4, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="UTIL", row=4, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="IMOB", row=5, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="IFNC", row=5, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="IEEX", row=6, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="IMAT", row=6, col=2, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=6, col=1, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=6, col=2, title_font=dict(size=16))
fig.update_legends(font=dict(size=15))
fig.update_annotations(dict(
    xref="paper", yref="paper",
    x=0, y=-0.1,
))




# Exiba os subplots
fig.show()

print('Linhas de Avanço e Declínio (LAD):')
print('$IBRA','$IBOV','$SMLL','$ICON','$MLCX','$IDIV','$INDX','$UTIL','$IMOB','$IFNC','$IEEX','$IMAT')
