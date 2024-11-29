import os
import glob
import pandas as pd
import datetime

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
print("15 - TODOS")

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
    15: "TODOS",
}

# Verifica se o código digitado pelo usuário está no dicionário
if codigo in indices:
    indice = indices[codigo]
    print(f"Você selecionou o índice {indice}.")
else:
    print("Código de índice inválido.")

# Agora, a variável "indice" contém o código selecionado (ou é None se o código for inválido)







# Lista de arquivos CSV na pasta
list_of_files = glob.glob(f"C:/Users/armen/OneDrive/Estratégias/Listas/{indice}/*")

# Encontre o arquivo mais recente na lista
latest_file = max(list_of_files, key=os.path.getctime)

# Leia o arquivo mais recente em um DataFrame
lista = pd.read_csv(latest_file, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python',
                    thousands='.', decimal=',', header=1, index_col=False)

# Crie um DataFrame a partir da coluna 'Código'
df = pd.DataFrame(lista)
codigo_list = df['Código']

# Crie um conjunto para armazenar os valores de data únicos
datas_unicas = set()

# Itere sobre os códigos e verifique as datas dos arquivos CSV correspondentes
for codigo in codigo_list:
    arquivo_csv = f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{codigo}_B_0_Diário.csv"
    print(codigo)
    if os.path.isfile(arquivo_csv):
        acn = pd.read_csv(arquivo_csv, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=0, engine='python',
                          thousands='.', decimal=',', header=0, index_col=False)
        df1 = pd.DataFrame(acn)
        df1['Data'] = pd.to_datetime(df1['Data'], format="%d/%m/%Y")
        df1 = df1.sort_values(by=["Data"], ascending=True)
        # Adicione a última data do DataFrame atual ao conjunto
        datas_unicas.add(df1['Data'].iloc[-1])

# Crie um dicionário para armazenar as datas e os códigos correspondentes
datas_e_codigos = {}

# Itere sobre os códigos e verifique as datas dos arquivos CSV correspondentes
for codigo in codigo_list:
    arquivo_csv = f"C:/Users/armen/OneDrive/Estratégias/Base/Diária/{codigo}_B_0_Diário.csv"
    print(codigo)
    if os.path.isfile(arquivo_csv):
        acn = pd.read_csv(arquivo_csv, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=0, engine='python',
                          thousands='.', decimal=',', header=0, index_col=False)
        df1 = pd.DataFrame(acn)
        df1['Data'] = pd.to_datetime(df1['Data'], format="%d/%m/%Y")
        df1 = df1.sort_values(by=["Data"], ascending=True)
        # Adicione a última data do DataFrame atual ao dicionário
        datas_e_codigos[df1['Data'].iloc[-1]] = codigo

print(datas_e_codigos)



# Verifique se todas as datas são iguais
if len(datas_unicas) == 1:
    data_igual = datas_unicas.pop()
    # Formate a data no formato especificado (d%/m%/a%)
    data_formatada = data_igual.strftime("%d/%m/%Y")
    print(f"{data_formatada} ok - Diário")
else:
    print("Os valores de data no Diário não são iguais em todos os arquivos.")

    
# Itere sobre as datas únicas e converta cada valor de string para datetime
for data_str in datas_unicas:
    data = datetime.datetime.strptime(data_str, "%d/%m/%Y")
    print(data.strftime("%d/%m/%Y"))



# Crie um conjunto para armazenar os valores de data únicos
datas_unicas1 = set()

# Itere sobre os códigos e verifique as datas dos arquivos CSV correspondentes
for codigo in codigo_list:
    arquivo_csv1 = (
        f"C:/Users/armen/OneDrive/Estratégias/Base/Semanal/{codigo}_B_0_Semanal.csv"
    )
    if os.path.isfile(arquivo_csv1):
        acn1 = pd.read_csv(
            arquivo_csv1,
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
        df2 = pd.DataFrame(acn1)
        df2["Data"] = pd.to_datetime(df2["Data"], format="%d/%m/%Y")
        df2 = df2.sort_values(by=["Data"], ascending=True)
        # Adicione a última data do DataFrame atual ao conjunto
        datas_unicas1.add(df2["Data"].iloc[-1])

# Verifique se todas as datas são iguais
if len(datas_unicas1) == 1:
    data_igual = datas_unicas1.pop()
    # Formate a data no formato especificado (d%/m%/a%)
    data_formatada = data_igual.strftime("%d/%m/%Y")
    print(f"{data_formatada} ok - Diário")
else:
    print("Os valores de data no Semanal não são iguais em todos os arquivos.")


# Itere sobre as datas únicas e converta cada valor de string para datetime
for data_str1 in datas_unicas1:
    data1 = datetime.datetime.strptime(data_str1, "%d/%m/%Y")
    print(data1.strftime("%d/%m/%Y"))

