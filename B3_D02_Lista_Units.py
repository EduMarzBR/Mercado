import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


# Instale o driver do Chrome
chrome_driver_path = ChromeDriverManager().install()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# URL base da página
base_url = "https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/units/"
page = 1  # Número da página inicial

# Abrir o arquivo CSV para escrita
with open("dados_units.csv", "w", newline="", encoding="ISO-8859-1") as csvfile:
    fieldnames = [
        "Nome de Pregão",
        "Código da Unit",
        "Composição",
    ]  # Defina os campos que deseja salvar
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()  # Escreve os cabeçalhos dos campos




    s = Service(ChromeDriverManager().install())
    wd = webdriver.Chrome(service=s)

    # Construir a URL da página atual
    url = f"{base_url}"

    # Abrir a página
    wd.get(url)



    # Aguardar até que a tabela seja carregada

    # Configurar o WebDriver e o tempo de espera
    wait = WebDriverWait(wd, 20)

    try:
        # Esperar até que o elemento com a classe 'responsive' esteja presente no DOM e visível
        table = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".responsive"))
        )

        # Encontrar todas as linhas da tabela
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Processar as linhas conforme necessário

        for idx, row in enumerate(rows):
            # Pular a primeira linha (cabeçalhos das colunas)
            if idx == 0:
                continue

            # Encontrar as células da linha
            cells = row.find_elements(By.TAG_NAME, "td")

            # Extrair os dados das células e escrever no arquivo CSV
            Nome_De_Pregao = cells[0].text
            Codigo = cells[1].text
            Composicao = cells[2].text

            writer.writerow(
                {
                    "Nome de Pregão": Nome_De_Pregao,
                    "Código da Unit": Codigo,
                    "Composição": Composicao,
                }
            )


    except TimeoutException:
        print("O elemento não foi encontrado dentro do tempo especificado.")

    # Iterar pelas linhas da tabela

    wd.quit()
