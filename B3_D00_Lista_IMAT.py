from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from time import sleep
import os
import shutil

def listacoes(lista):
    s = Service(ChromeDriverManager().install())
    wd = webdriver.Chrome(service=s)
    wd.get("https://sistemaswebb3-listados.b3.com.br/indexPage/day/"+lista+"?language=pt-br")
    sleep(5)
    wd.find_element(By.ID, "segment").send_keys("Setor de Atuação")
    sleep(5)
    wd.find_element(By.PARTIAL_LINK_TEXT, "Download").click()
    sleep(5)
    wd.quit()  # Encerrar o navegador

    source_dir = r"C:\Users\armen\Downloads"
    destination_dir = r"C:\Users\armen\OneDrive\Estratégias\Listas\IMAT"

    # Listar arquivos .csv no diretório de origem
    csv_files = [f for f in os.listdir(source_dir) if f.endswith(".csv")]

    if csv_files:
        # Ordenar arquivos pelo tempo de modificação mais recente
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(source_dir, x)))

        # Pegar o arquivo mais recente
        latest_file = csv_files[-1]
        source_path = os.path.join(source_dir, latest_file)
        destination_path = os.path.join(destination_dir, latest_file)

        # Excluir o arquivo .csv existente no destino, se houver
        if os.path.exists(destination_path):
            os.remove(destination_path)

        # Mover o arquivo baixado para o destino
        shutil.move(source_path, destination_path)

listacoes("IMAT")
