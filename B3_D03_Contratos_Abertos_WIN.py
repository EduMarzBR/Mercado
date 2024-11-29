from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd





s = Service(ChromeDriverManager().install())
wd = webdriver.Chrome(service=s)
wd.get("https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-tipo-de-participante-ptBR.asp")
sleep(5)





# Localiza a tabela pelo Xpath
table_xpath = 'responsive'
tables = wd.find_elements(By.CLASS_NAME, table_xpath)
caps=wd.find_elements(By.TAG_NAME, "caption")
table_data_win = []
table_data_ind = []




for table, cap in zip(tables, caps):
    if cap.text == "MERCADO FUTURO FRACIONÁRIO DE IBOVESPA MINI":


        # Extrai todas as linhas da tabela
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Lista para armazenar os dados


        # Para cada linha, extraímos os dados das colunas (td ou th)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            table_data_win.append([cell.text for cell in cells])
        break

for table, cap in zip(tables, caps):
    if cap.text == "MERCADO FUTURO DE IBOVESPA":


        # Extrai todas as linhas da tabela
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Lista para armazenar os dados


        # Para cada linha, extraímos os dados das colunas (td ou th)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            table_data_ind.append([cell.text for cell in cells])
        break

# Fecha o navegador
wd.quit()

# Transforma os dados da tabela win em um DataFrame
df_win = pd.DataFrame(table_data_win)
df_win = df_win.dropna()
df_win = df_win.drop(df_win.columns[[2,4]], axis=1)

colunas = ["Tipo de Participante", "Compra_win", "Venda_win"]

df_win.columns = colunas

df_win["Compra_win"] = df_win["Compra_win"].str.replace(".", "")
df_win["Venda_win"] = df_win["Venda_win"].str.replace(".", "")
df_win["Compra_win"] = pd.to_numeric(df_win["Compra_win"])
df_win["Compra_win"] = df_win["Compra_win"].apply(lambda x: x/5)
df_win["Venda_win"] = pd.to_numeric(df_win["Venda_win"])
df_win["Venda_win"] = df_win["Venda_win"].apply(lambda x: x/5)



# Transforma os dados da tabela ind em um DataFrame

df_ind = pd.DataFrame(table_data_ind)
df_ind = df_ind.dropna()
df_ind = df_ind.drop(df_ind.columns[[2,4]], axis=1)

colunas = ["Tipo de Participante", "Compra_ind", "Venda_ind"]

df_ind.columns = colunas

df_ind["Compra_ind"] = df_ind["Compra_ind"].str.replace(".", "")
df_ind["Venda_ind"] = df_ind["Venda_ind"].str.replace(".", "")
df_ind["Compra_ind"] = pd.to_numeric(df_ind["Compra_ind"])
df_ind["Venda_ind"] = pd.to_numeric(df_ind["Venda_ind"])

# Junta os dois DataFrames: win e ind

df_atual = pd.merge(df_win, df_ind, on="Tipo de Participante")

df_atual["Compra atual"] = df_atual["Compra_win"] + df_atual["Compra_ind"]
df_atual["Venda atual"] = df_atual["Venda_win"] + df_atual["Venda_ind"]

df_atual = df_atual.drop(["Compra_win", "Venda_win", "Compra_ind", "Venda_ind"], axis=1)

df_atual["Saldo atual"] = df_atual["Compra atual"] - df_atual["Venda atual"]

##################################### Dia anterior

s = Service(ChromeDriverManager().install())
wd = webdriver.Chrome(service=s)
wd.get("https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-tipo-de-participante-ptBR.asp")
sleep(5)


data = input("Digite a data anterior (DD/MM/AAAA): ")
wd.find_element(By.ID, "dData1").send_keys(data)
wd.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/form/div/div[2]").click()


# Localiza a tabela pelo Xpath
table_xpath = 'responsive'
tables = wd.find_elements(By.CLASS_NAME, table_xpath)
caps=wd.find_elements(By.TAG_NAME, "caption")


table_data_win = []
table_data_ind = []




for table, cap in zip(tables, caps):
    if cap.text == "MERCADO FUTURO FRACIONÁRIO DE IBOVESPA MINI":


        # Extrai todas as linhas da tabela
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Lista para armazenar os dados


        # Para cada linha, extraímos os dados das colunas (td ou th)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            table_data_win.append([cell.text for cell in cells])
        break

for table, cap in zip(tables, caps):
    if cap.text == "MERCADO FUTURO DE IBOVESPA":


        # Extrai todas as linhas da tabela
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Lista para armazenar os dados


        # Para cada linha, extraímos os dados das colunas (td ou th)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            table_data_ind.append([cell.text for cell in cells])
        break

# Fecha o navegador
wd.quit()

# Transforma os dados da tabela win em um DataFrame
df_win = pd.DataFrame(table_data_win)
df_win = df_win.dropna()
df_win = df_win.drop(df_win.columns[[2,4]], axis=1)

colunas = ["Tipo de Participante", "Compra_win", "Venda_win"]

df_win.columns = colunas

df_win["Compra_win"] = df_win["Compra_win"].str.replace(".", "")
df_win["Venda_win"] = df_win["Venda_win"].str.replace(".", "")
df_win["Compra_win"] = pd.to_numeric(df_win["Compra_win"])
df_win["Compra_win"] = df_win["Compra_win"].apply(lambda x: x/5)
df_win["Venda_win"] = pd.to_numeric(df_win["Venda_win"])
df_win["Venda_win"] = df_win["Venda_win"].apply(lambda x: x/5)



# Transforma os dados da tabela ind em um DataFrame

df_ind = pd.DataFrame(table_data_ind)
df_ind = df_ind.dropna()
df_ind = df_ind.drop(df_ind.columns[[2,4]], axis=1)

colunas = ["Tipo de Participante", "Compra_ind", "Venda_ind"]

df_ind.columns = colunas

df_ind["Compra_ind"] = df_ind["Compra_ind"].str.replace(".", "")
df_ind["Venda_ind"] = df_ind["Venda_ind"].str.replace(".", "")
df_ind["Compra_ind"] = pd.to_numeric(df_ind["Compra_ind"])
df_ind["Venda_ind"] = pd.to_numeric(df_ind["Venda_ind"])

# Junta os dois DataFrames: win e ind

df_anterior = pd.merge(df_win, df_ind, on="Tipo de Participante")

df_anterior["Compra anterior"] = df_anterior["Compra_win"] + df_anterior["Compra_ind"]
df_anterior["Venda anterior"] = df_anterior["Venda_win"] + df_anterior["Venda_ind"]

df_anterior = df_anterior.drop(["Compra_win", "Venda_win", "Compra_ind", "Venda_ind"], axis=1)

df_anterior["Saldo anterior"] = df_anterior["Compra anterior"] - df_anterior["Venda anterior"]



df = pd.merge(df_atual, df_anterior, on="Tipo de Participante", how="outer")
df["Compra Líquida"] = df["Compra atual"] - df["Compra anterior"]
df["Venda Líquida"] = df["Venda atual"] - df["Venda anterior"]
df["Variação"] = df["Compra Líquida"] - df["Venda Líquida"]
print(df)



