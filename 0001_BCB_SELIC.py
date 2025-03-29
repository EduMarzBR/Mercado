from bcb import sgs
import pandas as pd

selic = sgs.get({'SELIC':432}, start='2022-01-01')

selic = pd.DataFrame(selic)
selic["SELIC Dia"] = (1+selic["SELIC"]/100)**(252)-1
selic_hoje = selic["SELIC"].iloc[-1]


selic.to_csv("C:/Users/armen/OneDrive/Estratégias/Fundos/Diaria/selic.csv",
           encoding="ISO-8859-1",
    )

print(f"selic hoje = {round(selic_hoje,2)} %a.a. ", )
