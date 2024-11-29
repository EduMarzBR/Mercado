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
        if setores.loc[i,"Unnamed: 0"] == "SETOR ECONÔMICO":
            setores[i + 1,"Unnamed: 0"] = ""
        elif pd.notna(setores.loc[i, "Unnamed: 0"]):
            continue
        elif pd.isna(setores.loc[i,"Unnamed: 0"]):
            setores.loc[i,"Unnamed: 0"] = setores.loc[i - 1,"Unnamed: 0"]

    for i in range(0, len(setores["Unnamed: 3"])):
        if setores.loc[i,"Unnamed: 1"] == "SUBSETOR":
            setores.loc[i + 1,"Unnamed: 1"] = ""
        elif pd.notna(setores.loc[i, "Unnamed: 1"]):
            setores.loc[i,"Unnamed: 1"] = setores.loc[i,"Unnamed: 1"]
        elif pd.isna(setores.loc[i, "Unnamed: 1"]):
            setores.loc[i,"Unnamed: 1"] = setores.loc[i - 1,"Unnamed: 1"]

    for i in range(0, len(setores["Unnamed: 3"])):
        if setores.loc[i,"Unnamed: 2"] == "SEGMENTO":
            setores.loc[i,"Unnamed: 5"] = "SEGMENTO"
            setores.loc[i,"Unnamed: 2"] = "CIA"
        elif (
            pd.notna(setores.loc[i,"Unnamed: 2"])
            and pd.isna(setores.loc[i,"Unnamed: 3"])
            and pd.isna(setores.loc[i,"Unnamed: 4"])
        ):
            setores.loc[i,"Unnamed: 5"] = setores.loc[i,"Unnamed: 2"]
        elif pd.notna(setores.loc[i, "Unnamed: 2"]) and pd.notna(setores.loc[i, "Unnamed: 3"]):
            setores.loc[i,"Unnamed: 5"] = setores.loc[i - 1,"Unnamed: 5"]
        elif (
            pd.isna(setores.loc[i,"Unnamed: 2"])
            and pd.notna(setores.loc[i,"Unnamed: 3"])
            and pd.notna(setores.loc[i,"Unnamed: 4"])
        ):
            setores.loc[i,"Unnamed: 5"] = ""
        elif (
            pd.isna(setores.loc[i,"Unnamed: 2"])
            and pd.isna(setores.loc[i,"Unnamed: 3"])
            and pd.isna(setores.loc[i,"Unnamed: 4"])
        ):
            setores.loc[i,"Unnamed: 5"] = ""

    for i in range(0, len(setores["Unnamed: 3"])):
        if (
            setores.loc[i,"Unnamed: 3"] == "LISTAGEM"
            or setores.loc[i, "Unnamed: 3"] == "CÓDIGO"
        ):
            setores.drop(i, inplace=True)
        elif pd.isna(setores.loc[i,"Unnamed: 3"]):
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
