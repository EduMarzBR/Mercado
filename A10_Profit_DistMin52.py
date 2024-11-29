import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import os
import glob
import ta
import talib



list_of_files = glob.glob("C:/Users/armen/OneDrive/Estratégias/Listas/IBRA/*") # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getctime)

lista= pd.read_csv(latest_file, sep=';', encoding='ISO-8859-1',skiprows = 0, skipfooter=2, engine='python', thousands='.',decimal=',', header=1, index_col=False)
df = pd.DataFrame(lista)
lista = df['Código']
lista.to_excel("Código.xlsx")



dist_mn_t=[]
dist_mn_y=[]
asset=[]

for x in lista:
    acn = pd.read_csv("C:/Users/armen/OneDrive/Estratégias/Base/Diária/" + x + "_B_0_Diário.csv", sep=';',
                      encoding='ISO-8859-1', skiprows=0, skipfooter=2, engine='python', thousands='.', decimal=',',
                      header=0, index_col=False)
    df = pd.DataFrame(acn)
    df = df.iloc[0:251]

    df['Data'] = pd.to_datetime(df['Data'], format="%d/%m/%Y")

    df = df.sort_values(by=['Data'], ascending=True)

    mn= df['Fechamento'].min()
    tdy=df['Fechamento'].iloc[-1]
    dist_t = round(((tdy-mn)/mn)*100,2)

    ystd = df['Fechamento'].iloc[-2]
    dist_y = round(((ystd - mn) / mn) * 100, 2)


    dist_mn_t.append(dist_t)
    asset.append(x)

    dist_mn_y.append(dist_y)


    df3=pd.DataFrame(dist_mn_t)
    df3.index.name="Indice"
    df2=pd.DataFrame(asset)
    df2.index.name = "Indice"
    df1=pd.DataFrame(dist_mn_y)
    df1.index.name = 'Indice'
    df2 = pd.merge(df2, df1, how="left", on="Indice")
    df3 = pd.merge(df2,df3,how='left', on='Indice')
    df3.rename(columns={'0_x': 'Ativo', '0_y': 'Preg. Anterior',0:'Hoje'}, inplace=True)
    df3.set_index(['Ativo'], inplace=True)
    dmax = df3.nlargest(10, 'Hoje')
    dmin = df3.nsmallest(10,'Hoje')
    


    # dmin=df2.nsmallest(5,'Dist %')




print('--------------------------------')
print('    10 ativos mais distantes')
print('  da mínima das últimas 52 semanas        ')
print('--------------------------------')
print (dmax)
print('--------------------------------')
print('')
print('--------------------------------')
print('    10 ativos mais próximos ')
print('  da mínima das últimas 52 semanas        ')
print('--------------------------------')
print(dmin)
print('--------------------------------')
