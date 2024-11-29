import glob
import os
import pandas as pd
import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from B3_D01_Setores import setores


def esquerda(texto, num_caracteres):
    return texto[:num_caracteres]


# pergunta qual o índice que vc quer
ind = None

while ind not in [1, 2]:
    ind = int(input("Escolha os seguintes índices: 1 - IBOV, 2 - IBRA: "))

    if ind == 1:
        ind1 = "IBOV"
    elif ind == 2:
        ind1 = "IBRA"
    else:
        print("Escolha inválida. Por favor, escolha 1 ou 2.")

# pergunta o time frame que vc quer

tfi = None


while tfi not in [1, 2]:
    tfi = int(input("Escolha os seguintes time frames: 1 - Diário, 2 - Semanal: "))

    if tfi == 1:
        tf = "Diária"
        tf1 = "Diário"
    elif tfi == 2:
        tf = "Semanal"
        tf1 = "Semanal"
    else:
        print("Escolha inválida. Por favor, escolha 1 ou 2.")


mma = 30

# Traz a data atual
data_atual = datetime.now()
dt = data_atual.strftime("%d/%m/%Y")


# Carregar a lista de ativo do índice escolhido

list_of_files = glob.glob(
    f"C:/Users/armen/OneDrive/Estratégias/Listas/{ind1}/*"
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

# Carregar a lista de ações da B3 com os seus respectivos setores
setores = pd.DataFrame(setores())
# Mudar o nome das colunas para coincidir com o nome da coluna na outra lista e assim juntar as duas listas
setores = setores.rename(columns={"Código": "Cod. Emp."})

df["Cod. Emp."] = df["Código"].apply(esquerda, args=(4,))
# Junta a lista de ações do IBRA com a lista de ações com os seus respectivos setores
df = pd.merge(df, setores, on="Cod. Emp.", how="left")
df = df.drop(columns=["Setor_x", "Empresa", "Segmento"])

# Criar listas com as ações de cada setor
setores_lista = df["Setor_y"].dropna().unique()



lad = []
# Cria lista vazia para armazenar as tendências de alta e baixa no curto  prazo para cada dia
tendencias = []
for setor in setores_lista:
    lista_setor = df.loc[df["Setor_y"] == setor]
    acoes = lista_setor["Código"]
    pesos = lista_setor["Part. (%)"]
    # Calcular os avanços e declínios de cada dia
    dfs_temp = []
    tendencia = []
    for acao, peso in zip(acoes, pesos):
        acn = pd.read_csv(
            f"C:/Users/armen/OneDrive/Estratégias/Base/{tf}/"
            + acao
            + f"_B_0_{tf1}.csv",
            sep=";",
            encoding="ISO-8859-1",
            skiprows=0,
            skipfooter=0,
            engine="python",
            thousands=".",
            decimal=",",
            header=0,
            index_col=False,
        )

        df0 = pd.DataFrame(acn)
        df0["Data"] = pd.to_datetime(df0["Data"], format="%d/%m/%Y")
        df0 = df0.sort_values(by=["Data"], ascending=True)
        df0.set_index("Data", inplace=True)

        df1 = pd.DataFrame(acn)
        df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")
        df1 = df1.sort_values(by=["Data"], ascending=True)
        df1.set_index("Data", inplace=True)

        # Calcular a tendência dos ativos

        df0["mme9"] = df0["Fechamento"].ewm(span=9, adjust=True).mean()
        df0["mme21"] = df0["Fechamento"].ewm(span=21, adjust=True).mean()

        if (
            df0["Fechamento"].iloc[-1] > df0["mme9"].iloc[-1]
            and df0["mme9"].iloc[-1] > df0["mme21"].iloc[-1]
        ):
            tendencia.append([f"${acao}", setor, "Alta"])
        elif (
            df0["Fechamento"].iloc[-1] < df0["mme9"].iloc[-1]
            and df0["mme9"].iloc[-1] < df0["mme21"].iloc[-1]
        ):
            tendencia.append([f"${acao}", setor, "Baixa"])
        else:
            tendencia.append([f"${acao}", setor, "Neutra"])

        # Calcular a coluna "signal" da LAD
        condition_1 = df1["Fechamento"].diff()

        df1["signal"] = condition_1 > 0

        # Armazenar o DataFrame temporário na lista
        dfs_temp.append(df1["signal"].astype(int).apply(lambda x: x * peso if x==1 else -peso))

    df_tendencias = pd.DataFrame(tendencia)
    df_tendencias = df_tendencias.rename(
        columns={0: "Código", 1: "Setor", 2: "Tendência"}
    )

    tendencias.append(df_tendencias[["Código", "Setor", "Tendência"]])
    # Concatenar os DataFrames temporários para criar df3
    df3 = pd.concat(dfs_temp, axis=1)

    # Substituir 0 por -1 em todo o DataFrame
    df3.replace(0, -1, inplace=True)




    # Calcular a coluna "Soma" usando a vetorização
    df3["Soma"] = df3.sum(axis=1)

    # Calcular a coluna "addc", LAD
    df3["addc1"] = df3["Soma"].cumsum()

    df3["addc"] = df3["addc1"].ewm(span=9, adjust=True).mean()

    # Calcular a média móvel de addc, LAD
    df3["addc_MMA"] = df3["addc"].rolling(window=mma).mean()
    df3.rename(
        columns={"addc": f"addc_{setor}", "addc_MMA": f"addc_MMA_{setor}"}, inplace=True
    )

    # Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
    df3_250 = df3.iloc[-150:]
    lad.append(df3_250[[f"addc_{setor}", f"addc_MMA_{setor}"]])


tend_all = pd.concat(tendencias)

lad_all = pd.concat(lad, axis=1)

lad_all = pd.DataFrame(lad_all)

df4 = pd.DataFrame(lad_all)

print(f"Percentual de ações do ${ind1} em tendência de alta dentro de cada setor - {dt}")
for setor in setores_lista:
    list_setor_alta = tend_all[
        (tend_all["Setor"] == setor) & (tend_all["Tendência"] == "Alta")
    ]
    list_setor_alta = list_setor_alta["Código"].tolist()
    lista_todo_setor = tend_all[(tend_all["Setor"] == setor)]["Código"].tolist()
    perct_tend_alta = round((len(list_setor_alta) / len(lista_todo_setor)) * 100, 2)
    print("")
    print(setor)
    print(f"{perct_tend_alta} % do setor em tendência Alta: {list_setor_alta}")


# listar todos os ativos que compõem o IBRA
lista_ibra = df["Código"]
dfs_temp1 = []
for acao_ibra in lista_ibra:
    acn = pd.read_csv(
        f"C:/Users/armen/OneDrive/Estratégias/Base/{tf}/"
        + acao_ibra
        + f"_B_0_{tf1}.csv",
        sep=";",
        encoding="ISO-8859-1",
        skiprows=0,
        skipfooter=0,
        engine="python",
        thousands=".",
        decimal=",",
        header=0,
        index_col=False,
    )
    df1 = pd.DataFrame(acn)
    df1["Data"] = pd.to_datetime(df1["Data"], format="%d/%m/%Y")
    df1 = df1.sort_values(by=["Data"], ascending=True)
    df1.set_index("Data", inplace=True)
    condition_1 = df1["Fechamento"].diff()
    df1["signal"] = condition_1 > 0
    # Armazenar o DataFrame temporário na lista
    dfs_temp1.append(df1["signal"].astype(int).apply(lambda x: x * peso if x==1 else -peso))

# Concatenar os DataFrames temporários para criar df3
df3 = pd.concat(dfs_temp1, axis=1)

# Substituir 0 por -1 em todo o DataFrame
#df3.replace(0, -1, inplace=True)

# Calcular a coluna "Soma" usando a vetorização
df3["Soma"] = df3.sum(axis=1)

# Calcular a coluna "addc", LAD
df3["addc1"] = df3["Soma"].cumsum()

df3["addc"] = df3["addc1"].ewm(span=9, adjust=True).mean()

# Calcular a média móvel de addc, LAD
df3["addc_MMA"] = df3["addc"].rolling(window=mma).mean()


# Ajuste o DataFrame resultados para incluir apenas os últimos 200 dias
df4_250 = df4.iloc[-150:]
df3_250 = df3.iloc[-150:]

# Crie subplots com três linhas (uma para cada gráfico)

fig = make_subplots(rows=5, cols=2, shared_xaxes=True)



# # Adicione o gráfico de linha da LAD IBOV
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Tecnologia da Informação"],
        mode="lines",
        name="LAD Tecnologia",
        line=dict(color="blue"),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Tecnologia da Informação"],
        mode="lines",
        name=f"MMA{mma} Tecnologia",
        line=dict(color="red"),
    ),
    row=1,
    col=1,
)
# # Adicione o gráfico de linha da LAD SMLL
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Consumo não Cíclico"],
        mode="lines",
        name="LAD Cons. Básico",
        line=dict(color="blue"),
    ),
    row=1,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Consumo não Cíclico"],
        mode="lines",
        name=f"MMA{mma} Cons. Básico",
        line=dict(color="red"),
    ),
    row=1,
    col=2,
)
# # Adicione o gráfico de linha da LAD ICON
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Consumo Cíclico"],
        mode="lines",
        name="LAD Cons. Discricionário",
        line=dict(color="blue"),
    ),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Consumo Cíclico"],
        mode="lines",
        name=f"MMA{mma} Cons. Discricionário",
        line=dict(color="red"),
    ),
    row=2,
    col=1,
)
# # Adicione o gráfico de linha da LAD MLCX
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Financeiro"],
        mode="lines",
        name="LAD Financeiro",
        line=dict(color="blue"),
    ),
    row=2,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Financeiro"],
        mode="lines",
        name=f"MMA{mma} Financeiro",
        line=dict(color="red"),
    ),
    row=2,
    col=2,
)
# # Adicione o gráfico de linha da LAD IDIV
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Materiais Básicos"],
        mode="lines",
        name="LAD Mat. Básicos",
        line=dict(color="blue"),
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Materiais Básicos"],
        mode="lines",
        name=f"MMA{mma} Mat. Básicos",
        line=dict(color="red"),
    ),
    row=3,
    col=1,
)
# # Adicione o gráfico de linha da LAD INDX
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Petróleo, Gás e Biocombustíveis"],
        mode="lines",
        name="LAD Energia",
        line=dict(color="blue"),
    ),
    row=3,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Petróleo, Gás e Biocombustíveis"],
        mode="lines",
        name=f"MMA{mma} Energia",
        line=dict(color="red"),
    ),
    row=3,
    col=2,
)
# # Adicione o gráfico de linha da LAD UTIL
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Saúde"],
        mode="lines",
        name="LAD Saúde",
        line=dict(color="blue"),
    ),
    row=4,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Saúde"],
        mode="lines",
        name=f"MMA{mma} Saúde",
        line=dict(color="red"),
    ),
    row=4,
    col=1,
)
# # Adicione o gráfico de linha da LAD IMOB
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Comunicações"],
        mode="lines",
        name="LAD Comunicações",
        line=dict(color="blue"),
    ),
    row=4,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Comunicações"],
        mode="lines",
        name=f"MMA{mma} Comunicações",
        line=dict(color="red"),
    ),
    row=4,
    col=2,
)
# # Adicione o gráfico de linha da LAD IFNC
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Utilidade Pública"],
        mode="lines",
        name="LAD Util. Pública",
        line=dict(color="blue"),
    ),
    row=5,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Utilidade Pública"],
        mode="lines",
        name=f"MMA{mma} Util. Pública",
        line=dict(color="red"),
    ),
    row=5,
    col=1,
)
# # Adicione o gráfico de linha da LAD IEEX
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_Bens Industriais"],
        mode="lines",
        name="LAD Indústria",
        line=dict(color="blue"),
    ),
    row=5,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=df4_250.index,
        y=df4_250["addc_MMA_Bens Industriais"],
        mode="lines",
        name=f"MMA{mma} Indústria",
        line=dict(color="red"),
    ),
    row=5,
    col=2,
)


fig.add_annotation(
    text="Fonte: Nelogica e Eduardo Ohannes Marzbanian Neto, CNPI-P",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.1,
    showarrow=False,
    font=dict(size=14, color="gray"),
)


# Atualize as cores 'cor1' e 'cor2' com as cores desejadas, por exemplo, 'blue' e 'red'
fig.update_traces(marker=dict(size=10))
# Atualize os layouts dos subplots
fig.update_layout(
    title_text=f"Linhas de Avanço e Declínio setoriais do {ind1} - {dt}",
    title_font=dict(size=20),
)

fig.update_yaxes(title_text="Tecnologia", row=1, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Cons. Não Cíclico", row=1, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Cons. Cíclico", row=2, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Financeiro", row=2, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Mat. Básicos", row=3, col=1, title_font=dict(size=16))
fig.update_yaxes(
    title_text="Energia", row=3, col=2, title_font=dict(size=16)
)
fig.update_yaxes(title_text="Saúde", row=4, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Comunicações", row=4, col=2, title_font=dict(size=16))
fig.update_yaxes(title_text="Util. Pública", row=5, col=1, title_font=dict(size=16))
fig.update_yaxes(title_text="Indústria", row=5, col=2, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=5, col=1, title_font=dict(size=16))
fig.update_xaxes(title_text="Data", row=5, col=2, title_font=dict(size=16))
fig.update_legends(font=dict(size=15))
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


def situacao(lad, mma):
    if (lad_all[lad].iloc[-1] - lad_all[mma].iloc[-1]) / abs(
        lad_all[mma].iloc[-1]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (lad_all[lad].iloc[-1] - lad_all[mma].iloc[-1]) / abs(
            lad_all[mma].iloc[-1]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


def situacao_anterior(lad, mma):
    if (lad_all[lad].iloc[-2] - lad_all[mma].iloc[-2]) / abs(
        lad_all[mma].iloc[-2]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (lad_all[lad].iloc[-2] - lad_all[mma].iloc[-2]) / abs(
            lad_all[mma].iloc[-2]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


def situacao_index(lad, mma):
    if (df3_250[lad].iloc[-1] - df3_250[mma].iloc[-1]) / abs(
        df3_250[mma].iloc[-1]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (df3_250[lad].iloc[-1] - df3_250[mma].iloc[-1]) / abs(
            df3_250[mma].iloc[-1]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


def situacao_anterior_index(lad, mma):
    if (df3_250[lad].iloc[-2] - df3_250[mma].iloc[-2]) / abs(
        df3_250[mma].iloc[-2]
    ) > 0.01:
        situacao = "Positivo"
    else:
        if (df3_250[lad].iloc[-2] - df3_250[mma].iloc[-2]) / abs(
            df3_250[mma].iloc[-2]
        ) < -0.01:
            situacao = "Negativo"
        else:
            situacao = "Neutro"
    return situacao


situacao_ant_index = situacao_anterior_index("addc", "addc_MMA")
sit_index = situacao_index("addc", "addc_MMA")

sit_anterior_tecnologia = situacao_anterior(
    "addc_Tecnologia da Informação", "addc_MMA_Tecnologia da Informação"
)
sit_tecnologia = situacao(
    "addc_Tecnologia da Informação", "addc_MMA_Tecnologia da Informação"
)

sit_anterior_cons_basico = situacao_anterior(
    "addc_Consumo não Cíclico", "addc_MMA_Consumo não Cíclico"
)
sit_cons_basico = situacao("addc_Consumo não Cíclico", "addc_MMA_Consumo não Cíclico")

sit_anterior_cons_disc = situacao_anterior(
    "addc_Consumo Cíclico", "addc_MMA_Consumo Cíclico"
)
sit_cons_disc = situacao("addc_Consumo Cíclico", "addc_MMA_Consumo Cíclico")

sit_anterior_serv_financeiros = situacao_anterior(
    "addc_Financeiro", "addc_MMA_Financeiro"
)
sit_serv_financeiros = situacao("addc_Financeiro", "addc_MMA_Financeiro")

sit_anterior_mat_basicos = situacao_anterior(
    "addc_Materiais Básicos", "addc_MMA_Materiais Básicos"
)
sit_mat_basicos = situacao("addc_Materiais Básicos", "addc_MMA_Materiais Básicos")

sit_anterior_energia = situacao_anterior(
    "addc_Petróleo, Gás e Biocombustíveis", "addc_MMA_Petróleo, Gás e Biocombustíveis"
)
sit_energia = situacao(
    "addc_Petróleo, Gás e Biocombustíveis", "addc_MMA_Petróleo, Gás e Biocombustíveis"
)

sit_anterior_saude = situacao_anterior("addc_Saúde", "addc_MMA_Saúde")
sit_saude = situacao("addc_Saúde", "addc_MMA_Saúde")

sit_anterior_serv_comunicao = situacao_anterior(
    "addc_Comunicações", "addc_MMA_Comunicações"
)
sit_serv_comunicao = situacao("addc_Comunicações", "addc_MMA_Comunicações")

sit_anterior_util_pub = situacao_anterior(
    "addc_Utilidade Pública", "addc_MMA_Utilidade Pública"
)
sit_util_pub = situacao("addc_Utilidade Pública", "addc_MMA_Utilidade Pública")

sit_anterior_industrial = situacao_anterior(
    "addc_Bens Industriais", "addc_MMA_Bens Industriais"
)
sit_industrial = situacao("addc_Bens Industriais", "addc_MMA_Bens Industriais")

sit_lad = [
    sit_mat_basicos,
    sit_serv_comunicao,
    sit_cons_disc,
    sit_cons_basico,
    sit_energia,
    sit_serv_financeiros,
    sit_saude,
    sit_industrial,
    sit_tecnologia,
    sit_util_pub,
]
sit_anterior_lad = [
    sit_anterior_mat_basicos,
    sit_anterior_serv_comunicao,
    sit_anterior_cons_disc,
    sit_anterior_cons_basico,
    sit_anterior_energia,
    sit_anterior_serv_financeiros,
    sit_anterior_saude,
    sit_anterior_industrial,
    sit_anterior_tecnologia,
    sit_anterior_util_pub,
]
setores = [
    "Materiais Básicos",
    "Comunicação",
    "Consumo Cíclico",
    "Consumo Não Cíclico",
    "Energia",
    "Financeiro",
    "Saúde",
    "Indústria",
    "Tecnologia",
    "Utilidades Públicas",
]


sit_positivo = sit_lad.count("Positivo")
sit_negativo = sit_lad.count("Negativo")
sit_neutro = sit_lad.count("Neutro")


sit_total = sit_positivo + sit_negativo + sit_neutro
sit_positivo_perc = (sit_positivo / sit_total) * 100
sit_negativo_perc = (sit_negativo / sit_total) * 100
sit_neutro_perc = (sit_neutro / sit_total) * 100
print(f"")
print(f"")
print(f"UMA VISÃO SETORIAL DO MERCADO")
print(f"")
print(f"Linhas de Avanço e Declínio (LAD) | IBRA e Setores {dt}:")
print(f"")
print(f"$IBRA - Índice Brasil Amplo - {sit_index}")
print(f"Tecnologia - {sit_tecnologia}")
print(f"Consumo Não Cíclico - {sit_cons_basico}")
print(f"Consumo Cíclico - {sit_cons_disc}")
print(f"Financeiro - {sit_serv_financeiros}")
print(f"Materiais Básicos - {sit_mat_basicos}")
print(f"Energia - {sit_energia}")
print(f"Saúde - {sit_saude}")
print(f"Comunicação - {sit_serv_comunicao}")
print(f"Utilidades Públicas - {sit_util_pub}")
print(f"Indústria - {sit_industrial}")
print(f"")
print(f"Mudanças nas LADs:")
# Verifica se houve alguma mudanças na situação das LADs
setor_chg = []
for setor, lad, lad_ant in zip(setores, sit_lad, sit_anterior_lad):
    if lad != lad_ant:
        print(f"{setor} | {lad_ant} para {lad}")
        setor_chg.append(setor)
print(f"")
if len(setor_chg) == 0:
    print(f"Nenhuma mudança nas LADs.")
print(f"")

print(f"Situação geral:")
print(f"")
print(f"LADs Positivas: {sit_positivo} - {sit_positivo_perc:.2f}%")
print(f"LADs Negativas: {sit_negativo} - {sit_negativo_perc:.2f}%")
print(f"LADs Neutras: {sit_neutro} - {sit_neutro_perc:.2f}%")
print(f"")
print(f"O que é a LAD?")
print(
    f"A Linha de Avanço e Declínio (LAD) é uma ferramenta utilizada na análise técnica para avaliar a saúde geral do "
    f"mercado de ações. Ela compara o número de ações que estão em alta (avanço) com o número de ações que estão em "
    f"baixa (declínio) durante um determinado período. Neste estudo, o período é diário. Essa análise é comumente "
    f"aplicada ao mercado amplo, representado por índices, como o índice Brasil Amplo (IBRA) no Brasil ou o S&P 500 "
    f"nos Estados Unidos."
)
print(f"")
print(
    f"Se a Linha de Avanço estiver subindo, isso sugere que há mais ações em alta do que em baixa, indicando um "
    f"mercado mais forte. Por outro lado, se a Linha de Declínio estiver dominando, isso pode indicar fraqueza no "
    f"mercado."
)
print(f"")
print(
    f"A análise da Linha de Avanço e Declínio é frequentemente usada para identificar divergências entre o movimento "
    f"dos preços e a tendência subjacente do mercado, ajudando os investidores a tomarem decisões informadas sobre a "
    f"direção potencial do mercado de ações."
)
