import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import MetaTrader5 as mt5
from statsmodels.tsa.stattools import acf
from datetime import datetime
import pandas_market_calendars as mcal

mt5.initialize()

# pergunta qual o índice que vc quer
ind = None

while ind not in [1, 2]:
    ind = int(input("Escolha entre os seguintes contratos: 1 - WIN, 2 - WDO: "))

    if ind == 1:
        ind1 = "WIN$"
        ind2 = "Mini Índice"
    elif ind == 2:
        ind1 = "WDO$"
        ind2 = "Mini Dólar"
    else:
        print("Escolha inválida. Por favor, escolha 1 ou 2.")



# Função para estimar parâmetro de Hurst a partir dos dados históricos
def estimate_hurst(prices):
    """Estima o parâmetro de Hurst baseado na série histórica de preços."""
    log_returns = np.log(prices / prices.shift(1)).dropna()
    lags = np.arange(1, 31)  # Definir lags para análise
    autocorr = acf(log_returns, nlags=30, fft=True)

    # Ajuste de linha log-log para estimar Hurst
    log_lags = np.log(lags)
    log_autocorr = np.log(np.abs(autocorr[1 : len(lags) + 1]))  # Ignorar lag 0
    hurst, _ = np.polyfit(log_lags, log_autocorr, 1)

    return max(0.1, min(0.9, hurst))  # Limitar para intervalos realistas


# Função para gerar Movimento Browniano Fracionário (FBM) com memória histórica
def fbm_historical(n, hurst, delta, historical_increments):
    """Gera FBM com base em incrementos históricos para simular padrões passados."""
    historical_increments = historical_increments[
        -n:
    ]  # Seleciona os últimos `n` incrementos
    increments = historical_increments + np.random.standard_t(df=3, size=n) * delta
    fbm_values = np.cumsum(increments * np.arange(1, n + 1) ** hurst)
    return fbm_values
periodo = 3600
data_atual = datetime.now()
# Carregar dados históricos do Índice escolhido
ind = mt5.copy_rates_from(
        ind1, mt5.TIMEFRAME_M5, datetime.today(), periodo)

ind = pd.DataFrame(ind)
ind['time'] = pd.to_datetime(ind['time'], unit='s')  # Converter timestamps para datas
ind.set_index('time', inplace=True)
ind_fech = ind["close"]
ind_close = ind["close"]
last_price = ind_close.iloc[-1]

# Obter o calendário da B3
calendario_b3 = mcal.get_calendar("BMF")

# Criar um DataFrame com as datas úteis
start_date = ind_close.index[-1]
end_date = start_date + pd.Timedelta(days=30)  # Adicionar 30 dias como margem
schedule = calendario_b3.schedule(start_date=start_date, end_date=end_date)


# Estimativa de Hurst e parâmetros
hurst = estimate_hurst(ind_close)
print("Hurst:", hurst)
historical_increments = (
    np.log(ind_close / ind_close.shift(1)).dropna().values[-252:]  # Últimos 252 dias úteis
)
delta = np.std(historical_increments)

# Parâmetros para projeção
# Parâmetros para projeção
n = 126  # Número de intervalos de 5 minutos
num_simulations = 1000  # Número de trajetórias simuladas
util_dates = schedule.index  # Datas úteis no calendário B3
# Gerar datas úteis considerando 5 minutos
projection_dates = []
current_time = ind_close.index[-1]

# Gerar as próximas `n` datas úteis em intervalos de 5 minutos
while len(projection_dates) < n:
    current_time += pd.Timedelta(minutes=5)
    # Validar se é um dia útil no calendário B3
    valid_days = calendario_b3.valid_days(current_time.date(), current_time.date())
    if not valid_days.empty:  # Se for dia útil
        projection_dates.append(current_time)

# Converta para um índice do pandas
projection_dates = pd.to_datetime(projection_dates[:n])

# Simulações Fractais
simulations = []
for _ in range(num_simulations):
    fbm_projection = fbm_historical(n, hurst, delta, historical_increments)
    projection_prices = last_price * np.exp(fbm_projection)
    simulations.append(projection_prices)

# Converter para array para fácil manipulação
simulations = np.array(simulations)

# Calcular média e faixa de confiança
mean_projection = simulations.mean(axis=0)
lower_bound = np.percentile(simulations, 5, axis=0)
upper_bound = np.percentile(simulations, 95, axis=0)

# Gráfico ajustado
plt.figure(figsize=(12, 6))

# Plotar as trajetórias simuladas
for i in range(min(50, num_simulations)):
    plt.plot(projection_dates, simulations[i], color='orange', alpha=0.1)

# Adicionar faixa de confiança
plt.fill_between(
    projection_dates,
    lower_bound, upper_bound, color='lightblue', alpha=0.3, label='Faixa de Confiança (5%-95%)'
)

# Média das projeções
plt.plot(projection_dates, mean_projection, color='blue', label='Média das Projeções')

# Histórico do índice
plt.plot(ind_fech.index[-150:], ind_fech[-150:], label='Histórico do índice')

# Destacar o último valor da média das projeções
plt.scatter(projection_dates[-1], mean_projection[-1], color='red', zorder=5, label='Último Valor da Projeção')

# Exibir o valor numérico do último ponto da média das projeções
plt.text(
    projection_dates[-1],
    mean_projection[-1],
    f'{mean_projection[-1]:.2f}',
    color='red',
    ha='left',
    va='bottom',
    fontsize=10,
    fontweight='bold'
)

# Configurar título, rótulos e legenda
plt.title(f'Projeção Fractal Baseada no Histórico do {ind2} (6 Meses)')
plt.xlabel('Data')
plt.ylabel('Preço')
plt.legend()

# Adicionar grid
plt.grid(True, which='both', axis='both', linestyle='--', color='gray', linewidth=0.5)

# Mostrar o gráfico
plt.show()