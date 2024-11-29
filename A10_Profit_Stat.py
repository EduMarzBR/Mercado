import pandas as pd

# Carregar os dados históricos do Ibovespa (exemplo fictício)
# Substitua isso pelo carregamento real de dados do Ibovespa

benchmark = 'IBOV'
file_path = f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{benchmark}_B_0_Diário.csv"
df = pd.read_csv(
    file_path,
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


# Converter a coluna de data para o formato de data
df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")

# Ordenar o DataFrame pela coluna de data em ordem crescente
df = df.sort_values(by="Data")


df = pd.DataFrame(df)


# Encontrar a maior quantidade de dias seguidos de queda e as datas correspondentes
maior_queda = 0
contagem_atual = 0
data_inicio = None
datas_maior_queda = []

for i in range(1, len(df)):
    if df["Fechamento"].iloc[i] < df["Fechamento"].iloc[i - 1]:
        if contagem_atual == 0:
            data_inicio = df["Data"].iloc[i - 1]
        contagem_atual += 1
        if contagem_atual > maior_queda:
            maior_queda = contagem_atual
            datas_maior_queda = [data_inicio]
        elif contagem_atual == maior_queda:
            datas_maior_queda.append(data_inicio)
    else:
        contagem_atual = 0
        data_inicio = None

print(f"A maior quantidade de dias seguidos de queda foi {maior_queda} dias.")
print(f"Isso aconteceu {len(datas_maior_queda)} vezes nas seguintes datas:")
for data in datas_maior_queda:
    print(data)

# Encontrar a maior quantidade de dias seguidos de alta e as datas correspondentes
maior_alta = 0
contagem_atual = 0
data_inicio = None
datas_maior_alta = []

for i in range(1, len(df)):
    if df["Fechamento"].iloc[i] > df["Fechamento"].iloc[i - 1]:
        if contagem_atual == 0:
            data_inicio = df["Data"].iloc[i - 1]
        contagem_atual += 1
        if contagem_atual > maior_alta:
            maior_alta = contagem_atual
            datas_maior_alta = [data_inicio]
        elif contagem_atual == maior_alta:
            datas_maior_alta.append(data_inicio)
    else:
        contagem_atual = 0
        data_inicio = None

print(f"A maior quantidade de dias seguidos de alta foi {maior_alta} dias.")
print(f"Isso aconteceu {len(datas_maior_alta)} vezes nas seguintes datas:")
for data in datas_maior_alta:
    print(data)





