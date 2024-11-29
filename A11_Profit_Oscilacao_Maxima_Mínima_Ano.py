
import pandas as pd
import glob
import os
import pandas_market_calendars as mcal
from datetime import datetime, timedelta



# Configuração de variáveis
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

# Solicitação de índice ao usuário
codigo = int(input("Digite o número do índice desejado: "))

# Verificação do código do índice
if codigo in indices:
    indice = indices[codigo]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")

# Obtenção do arquivo mais recente para o índice selecionado
list_of_files = glob.glob(f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*")
latest_file = max(list_of_files, key=os.path.getctime)

# Leitura do arquivo CSV que contém a lista de ações do índice selecionado
acoes_df = pd.read_csv(
    latest_file,
    sep=";",
    encoding="ISO-8859-1",
    skiprows=0,
    skipfooter=2,
    engine="python",
    thousands=".",
    decimal=",",
    header=1,
)
acoes = acoes_df["Setor"].tolist()

# Obtenção de dados históricos para o período especificado

var_max_ano = []
var_min_ano = []
for ativo in acoes:
    # Caminho para a pasta que contém os arquivos CSV
    caminho_pasta = r"C:\Users\armen\OneDrive\Estratégias\Base\Diária"
    caminho_arquivo = os.path.join(caminho_pasta, f"{ativo}_B_0_Diário.csv")
    if os.path.exists(caminho_arquivo):
        df = pd.read_csv(
            caminho_arquivo,
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

        if df is not None and len(df) > 0:  # Verificação se df contém dados
            df = pd.DataFrame(df)
            # Converter a coluna de data para o formato de data
            df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")

            df_atual = df[df["Data"].dt.year == datetime.today().year]
            maxima_ano = df_atual["Máximo"].max()
            data_maxima_ano = df_atual[df_atual["Máximo"] == maxima_ano]["Data"].iloc[0]
            fechamento_atual = df_atual["Fechamento"].iloc[-1]

            variacao_da_maxima_ano = ((fechamento_atual - maxima_ano) / maxima_ano) * 100
            dias = (datetime.today() - data_maxima_ano).days
            var_max_ano.append([ativo, data_maxima_ano, variacao_da_maxima_ano, dias])
            #        print(f"{ativo} - {data_maxima_ano} - {variacao_da_maxima_ano} - {dias}")

            minima_ano = df_atual["Mínimo"].min()
            data_minima_ano = df_atual[df_atual["Mínimo"] == minima_ano]["Data"].iloc[0]
            fechamento_atual = df_atual["Fechamento"].iloc[-1]

            variacao_da_minima_ano = ((fechamento_atual - minima_ano) / minima_ano) * 100
            dias = (datetime.today() - data_minima_ano).days
            var_min_ano.append([ativo, data_minima_ano, variacao_da_minima_ano, dias])
    #        print(f"{ativo} - {data_minima_ano} - {variacao_da_minima_ano} - {dias}")

var_max_ano = pd.DataFrame(
    var_max_ano,
    columns=["Ativo", "Data da Máxima no Ano", "Variação", "Dias da Máxima no Ano"],
)
var_max_ano = var_max_ano.sort_values(by="Variação", ascending=False)

var_min_ano = pd.DataFrame(
    var_min_ano,
    columns=["Ativo", "Data da Mínima no Ano", "Variação", "Dias da Mínima no Ano"],
)
var_min_ano = var_min_ano.sort_values(by="Variação", ascending=False)


print("Ações que fizeram Máxima no Ano:")
max_ano_dia_atual = var_max_ano[var_max_ano["Dias da Máxima no Ano"] == 0]
print(max_ano_dia_atual)
print("")
print("Ações que fizeram Mínima no Ano:")
min_ano_dia_atual = var_min_ano[var_min_ano["Dias da Mínima no Ano"] == 0]
print(min_ano_dia_atual)
print("")
print("**Ações que fizeram Máxima e Mínima no Ano:**")
print("")
print(f"**{len(max_ano_dia_atual)} ações fizeram máxima no Ano**")
print(max_ano_dia_atual["Ativo"].tolist())
print("")
print(f"**{len(min_ano_dia_atual)} ações fizeram mínima no Ano**")
print(min_ano_dia_atual["Ativo"].tolist())
