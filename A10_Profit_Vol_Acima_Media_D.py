import os
import pandas as pd
import glob

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

print("")

list_of_files = glob.glob(rf"C:\Users\armen\OneDrive\Estratégias\Listas\{indice}\*")  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)


# Caminho para a pasta que contém os arquivos CSV
caminho_pasta = r"C:\Users\armen\OneDrive\Estratégias\Base\Diária"

# Lista de ativos
lista = pd.read_csv(latest_file, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python',
                    thousands='.', decimal=',', header=1, index_col=False)

df1 = pd.DataFrame(lista)

lista = df1['Código']




def calcular_diferenca_percentual(volume_atual, volume_medio):
    if volume_medio == 0:
        return 0
    return ((volume_atual - volume_medio) / volume_medio) * 100

print("")
for ativo in lista:
    # Montar o caminho completo do arquivo CSV
    caminho_arquivo = os.path.join(caminho_pasta, f"{ativo}_B_0_Diário.csv")

    #if os.path.exists(caminho_arquivo):
    if ativo != 'ISAE4':
        # Carregar o arquivo CSV utilizando o pandas
        df = pd.read_csv(caminho_arquivo, sep=';',
                      encoding='ISO-8859-1', skiprows=0, skipfooter=0, engine='python', thousands='.', decimal=',',
                      header=0, index_col=False)

        # Converter a coluna de data para o formato de data
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
        
        # Ordenar o DataFrame pela coluna de data em ordem crescente
        df = df.sort_values(by="Data")


        # Calcular o volume médio dos últimos 21 dias
        df["Volume Medio"] =df["Volume"].rolling(window=21).mean()

        # Obter o volume atual (do último dia)
        volume_atual = df.iloc[-1]["Volume"]
        volume_medio = df.iloc[-1]["Volume Medio"]
        # Comparar os volumes e calcular a diferença percentual
        diferenca_percentual = calcular_diferenca_percentual(volume_atual, volume_medio)

        # Calcular a variação de preço entre o fechamento do último dia e o dia anterior
        fechamento = df.iloc[-1]["Fechamento"]
        anterior = df.iloc[-2]["Fechamento"]
        var = calcular_diferenca_percentual(fechamento, anterior)


        # Imprimir os resultados


        if diferenca_percentual> 100:
            if var > 0:
                print(f"{ativo}:{diferenca_percentual:.2f}%: fechou em alta de: {var:.2f}%")
            elif var < 0:
                print(f"{ativo}:{diferenca_percentual:.2f}%: fechou em baixa de: {var:.2f}%")
            else:
                print(f"{ativo}:{diferenca_percentual:.2f}%: fechou estável:")

print("")
print('fonte: Eduardo Ohannes Marzbanian Neto CNPI-P e Nelógica')