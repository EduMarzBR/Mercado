import pandas as pd
import glob
import os

def setores():
    #Caminho da pasta onde se encontra o arquivo .xlsx
    path = r"C:\Users\armen\OneDrive\Estratégias\Listas\Setores"

    # Listar todos os arquivos .xlsx na pasta de download
    xlsx_files = glob.glob(os.path.join(path, "*.xlsx"))
    # Verificar se há arquivos .xlsx na pasta
    if not xlsx_files:
        print("Nenhum arquivo .xlsx encontrado.")
    else:
        # Encontrar o arquivo mais recente
        base_file = max(xlsx_files, key=os.path.getmtime)



    setores = pd.read_excel(base_file,
        header=5,
    )

    setores = pd.DataFrame(setores)

    setores["Unnamed: 5"] = ""

    for i in range(0, len(setores["Unnamed: 3"])):
        if setores["Unnamed: 0"][i] == "SETOR ECONÔMICO":
            setores["Unnamed: 0"][i + 1] = ""
        elif pd.notna(setores["Unnamed: 0"][i]):
            continue
        elif pd.isna(setores["Unnamed: 0"][i]):
            setores["Unnamed: 0"][i] = setores["Unnamed: 0"][i - 1]

    for i in range(0, len(setores["Unnamed: 3"])):
        if setores["Unnamed: 1"][i] == "SUBSETOR":
            setores["Unnamed: 1"][i + 1] = ""
        elif pd.notna(setores["Unnamed: 1"][i]):
            setores["Unnamed: 1"][i] = setores["Unnamed: 1"][i]
        elif pd.isna(setores["Unnamed: 1"][i]):
            setores["Unnamed: 1"][i] = setores["Unnamed: 1"][i - 1]

    for i in range(0, len(setores["Unnamed: 3"])):
        if setores["Unnamed: 2"][i] == "SEGMENTO":
            setores["Unnamed: 5"][i] = "SEGMENTO"
            setores["Unnamed: 2"][i] = "CIA"
        elif (
            pd.notna(setores["Unnamed: 2"][i])
            and pd.isna(setores["Unnamed: 3"][i])
            and pd.isna(setores["Unnamed: 4"][i])
        ):
            setores["Unnamed: 5"][i] = setores["Unnamed: 2"][i]
        elif pd.notna(setores["Unnamed: 2"][i]) and pd.notna(setores["Unnamed: 3"][i]):
            setores["Unnamed: 5"][i] = setores["Unnamed: 5"][i - 1]
        elif (
            pd.isna(setores["Unnamed: 2"][i])
            and pd.notna(setores["Unnamed: 3"][i])
            and pd.notna(setores["Unnamed: 4"][i])
        ):
            setores["Unnamed: 5"][i] = ""
        elif (
            pd.isna(setores["Unnamed: 2"][i])
            and pd.isna(setores["Unnamed: 3"][i])
            and pd.isna(setores["Unnamed: 4"][i])
        ):
            setores["Unnamed: 5"][i] = ""

    for i in range(0, len(setores["Unnamed: 3"])):
        if (
            setores["Unnamed: 3"][i] == "LISTAGEM"
            or setores["Unnamed: 3"][i] == "CÓDIGO"
        ):
            setores.drop(i, inplace=True)
        elif pd.isna(setores["Unnamed: 3"][i]):
            setores.drop(i, inplace=True)

    setores = setores.rename(
        columns={
            "Unnamed: 0": "Setor",
            "Unnamed: 1": "Subsetor",
            "Unnamed: 5": "Segmento",
            "Unnamed: 2": "Empresa",
            "Unnamed: 3": "Código",
            "Unnamed: 4": "Segmento Listagem",
        }
    )

    setores = setores[
        ["Código", "Empresa", "Setor", "Subsetor", "Segmento", "Segmento Listagem"]
    ]
    return setores


setores()
