from bcb import sgs
import pandas as pd

cdi = sgs.get({'CDI':12}, start='2022-01-01')

cdi = pd.DataFrame(cdi)
cdi["CDI Anual"] = (1+cdi["CDI"]/100)**(252)-1
cdi_hoje = cdi["CDI Anual"].iloc[-1]
cdi_dia = cdi["CDI"].iloc[-1]

cdi.to_csv("C:/Users/armen/OneDrive/Estratégias/Fundos/Diaria/cdi.csv",
           encoding="ISO-8859-1",
    )

print(f"CDI hoje = {round(cdi_hoje*100,2)} %a.a. ", )
print(f"CDI hoje = {round(cdi_dia,2)} %a.d")