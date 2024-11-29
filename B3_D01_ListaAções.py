from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from pathlib import Path
import os
import glob
import shutil


s = Service(ChromeDriverManager().install())
wd = webdriver.Chrome(service=s)
wd.get("https://arquivos.b3.com.br/?lang=pt")

#wd.find_element(By.PARTIAL_LINK_TEXT, "Baixar arquivo")
sleep(10)
# Esperar até que os elementos de download estejam presentes na página
elementos_download = WebDriverWait(wd, 20).until(
    EC.presence_of_all_elements_located((By.PARTIAL_LINK_TEXT, "Baixar arquivo"))
)

# Iterar sobre os elementos e clicar em cada um deles




for elemento in elementos_download:
    try:

        # Esperar até que o modal desapareça
        #WebDriverWait(wd, 5).until_not(
        #    EC.presence_of_element_located((By.CLASS_NAME, "modal"))
        #)
        sleep(20)
        # Clicar no link
        elemento.click()
        break

    except Exception as e:
        print(f"Erro ao clicar no elemento: {e}")


wd.quit()

# Mover arquivo para pasta de destino
lista_arquivos = glob.glob(os.path.join(r"C:\Users\armen\Downloads", "*"))

if not lista_arquivos:
    print("Nenhum arquivo encontrado na pasta de origem.")


# Encontrar o último arquivo modificado
ultimo_arquivo = max(lista_arquivos, key=os.path.getmtime)

# Construir o caminho de destino
caminho_destino = os.path.join(
    r"C:\Users\armen\OneDrive\Estratégias\Base\ListaAções",
    os.path.basename(ultimo_arquivo),
)

# Mover o arquivo para o destino
shutil.move(ultimo_arquivo, caminho_destino)

print(f"Arquivo movido de '{ultimo_arquivo}' para '{caminho_destino}'.")

list_acoes = pd.read_csv(
    caminho_destino,
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
list_acoes = pd.DataFrame(list_acoes)


list_acoes = list_acoes[
    (list_acoes["SgmtNm"] == "CASH")
    & (list_acoes["Asst"] != "TAXA")
    & list_acoes["SctyCtgyNm"].isin(["SHARES", "UNIT"])
]

list_acoes = list_acoes["TckrSymb"]
