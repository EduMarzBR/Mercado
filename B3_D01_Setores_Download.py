from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from time import sleep
import os
import zipfile
import requests
import glob


def download_setores():
    # Inicializa o serviço do ChromeDriver
    s = Service(ChromeDriverManager().install())

    # Cria uma instância do navegador Chrome usando o serviço configurado
    wd = webdriver.Chrome(service=s)

    # Acessa a URL especificada
    wd.get(
        "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/#accordionClassification"
    )

    # Aguarda 5 segundos para garantir que a página seja carregada completamente
    sleep(5)

    # Localiza e clica em um elemento específico na página usando XPath
    wd.find_element(
        By.XPATH,
        "/html/body/app-root/app-companies-home/div/div/div/div/div[2]/div[1]/div/div/a/h6",
    ).click()

    # Aguarda mais 5 segundos para garantir que a ação anterior tenha sido concluída
    sleep(5)

    # Encontra o elemento de link com o texto "Download" e obtém o atributo 'href' (URL)
    link_element = wd.find_element(By.XPATH, '//a[text()="Download"]')
    file_url = link_element.get_attribute("href")

    # Imprime o URL do link encontrado
    print(f"Link encontrado: {file_url}")

    # Fechar o navegador
    wd.quit()

    # Fazer o download do arquivo
    response = requests.get(file_url)
    response.raise_for_status()  # Verifica se a requisição foi bem-sucedida

    # Definir o diretório de download
    #Neste diretório não deve existir nenhum arquivo que não seja o arquivo .zip que será baixado e o arquivo .xlsx que
    # que será extraído, pois na segunda vez em que este código for executado, os arquivos .zip e .xlsx anteriorires
    # serão excluídos para em seguida baixar o novo arquivo .zip do qual será extraído o novo arquivo .xlsx.
    download_path = r"C:\Users\armen\OneDrive\Estratégias\Listas\Setores"

    # Listar todos os arquivos .xlsx na pasta de download
    xlsx_files = glob.glob(os.path.join(download_path, "*.xlsx"))

    # Verificar se há arquivos .xlsx na pasta
    if not xlsx_files:
        print("Nenhum arquivo .xlsx encontrado.")
    else:
        # Encontrar o arquivo mais antigo
        oldest_file = min(xlsx_files, key=os.path.getmtime)

        # Excluir o arquivo mais antigo
        os.remove(oldest_file)
        print(f"Arquivo excluído: {oldest_file}")

    # Listar todos os arquivos .zip na pasta
    zip_files = glob.glob(os.path.join(download_path, "*.zip"))

    # Verificar se há arquivos .zip na pasta
    if not zip_files:
        print("Nenhum arquivo .zip encontrado.")
    else:
        # Encontrar o arquivo mais antigo
        oldest_file = min(zip_files, key=os.path.getmtime)

        # Excluir o arquivo mais antigo
        os.remove(oldest_file)
        print(f"Arquivo excluído: {oldest_file}")

    # Nome do arquivo para salvar
    file_name = file_url.split("/")[-1]

    # Caminho completo do arquivo
    file_path = os.path.join(download_path, file_name)

    # Salvar o arquivo
    with open(file_path, "wb") as file:
        file.write(response.content)
    print(f"Arquivo baixado e salvo como: {file_name}")

    # Extrair o arquivo zip na pasta de download
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(download_path)
    print(f"Arquivo extraído para: {download_path}")

#chama a função para baixar o arquivo
download_setores()
