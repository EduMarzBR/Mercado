import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from statsmodels.tsa.stattools import acf
from datetime import datetime



# pergunta qual o índice que vc quer
ind = None

while ind not in [1, 2]:
    ind = int(input("Escolha os seguintes índices: 1 - IBOV, 2 - S&P 500: "))

    if ind == 1:
        ind1 = "^BVSP"
        ind2 = "IBOV"
    elif ind == 2:
        ind1 = "^GSPC"
        ind2 = "S&P 500"
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

data_atual = datetime.now()
# Carregar dados históricos do Índice escolhido
ind = yf.download(ind1, start="2022-01-01", end=data_atual)

ind_fech = ind["Adj Close"]
ind_close = ind["Adj Close"][:-100]
last_price = ind_close.iloc[-1]

# Estimativa de Hurst e parâmetros
hurst = estimate_hurst(ind_close)
print("Hurst:", hurst)
historical_increments = (
    np.log(ind_close / ind_close.shift(1)).dropna().values[-252:]  # Últimos 252 dias úteis
)
delta = np.std(historical_increments)

# Parâmetros para projeção
n = 126  # 6 meses úteis
num_simulations = 1000  # Número de trajetórias simuladas

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

# Gráfico das Simulações
plt.figure(figsize=(12, 6))

# Criar as datas correspondentes ao horizonte de projeção (n)
projection_dates = pd.date_range(ind_close.index[-1] + pd.Timedelta(days=1), periods=n, freq='B')

# Plot de trajetórias simuladas
for i in range(min(50, num_simulations)):
    plt.plot(projection_dates, simulations[i], color='orange', alpha=0.1)

# Adicionar faixa de confiança
plt.fill_between(
    projection_dates,
    lower_bound, upper_bound, color='lightblue', alpha=0.3, label='Faixa de Confiança (5%-95%)'
)

# Média das projeções
plt.plot(projection_dates, mean_projection, color='blue', label='Média das Projeções')

# Histórico do ind
plt.plot(ind_fech.index[-500:], ind_fech[-500:], label='Histórico do ind')

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

# Título, rótulos e legenda
plt.title(f'Projeção Fractal Baseada no Histórico do {ind2} (6 Meses)')
plt.xlabel('Data')
plt.ylabel('Preço')
plt.legend()

# Adicionar grids (mais detalhados)
plt.grid(True, which='both', axis='both', linestyle='--', color='gray', linewidth=0.5)

# Mostrar o gráfico
plt.show()
