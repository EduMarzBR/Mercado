import os
import pandas as pd
import glob

list_of_files = glob.glob(r"C:\Users\armen\OneDrive\Estratégias\Listas\IBRA\*")  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)


# Caminho para a pasta que contém os arquivos CSV
caminho_pasta = r"C:\Users\armen\OneDrive\Estratégias\Base\Mensal"

# Lista de ativos
lista = pd.read_csv(latest_file, sep=';', encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python',
                    thousands='.', decimal=',', header=1, index_col=False)

df1 = pd.DataFrame(lista)

lista = df1['Código']




def calcular_diferenca_percentual(volume_atual, volume_medio):
    if volume_medio == 0:
        return 0
    return ((volume_atual - volume_medio) / volume_medio) * 100


for ativo in lista:
    # Montar o caminho completo do arquivo CSV
    caminho_arquivo = os.path.join(caminho_pasta, f"{ativo}_B_0_Mensal.csv")

    if os.path.exists(caminho_arquivo):
        # Carregar o arquivo CSV utilizando o pandas
        df = pd.read_csv(caminho_arquivo, sep=';',
                      encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python', thousands='.', decimal=',',
                      header=0, index_col=False)

        # Converter a coluna de data para o formato de data
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
        
        # Ordenar o DataFrame pela coluna de data em ordem crescente
        df = df.sort_values(by="Data")

        # Filtrar as últimas 21 linhas (dias)
        ultimos_21_dias = df.tail(21)

        # Calcular o volume médio dos últimos 21 dias
        volume_medio = ultimos_21_dias["Volume"].mean()

        # Obter o volume atual (do último dia)
        volume_atual = df.iloc[-1]["Volume"]

        # Comparar os volumes e calcular a diferença percentual
        diferenca_percentual = calcular_diferenca_percentual(volume_atual, volume_medio)

        # Imprimir os resultados


        if diferenca_percentual> 100:

            print(f"{ativo}: {diferenca_percentual:.2f}%\n")

