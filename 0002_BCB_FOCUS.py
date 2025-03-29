import plotly.graph_objects as go
from bcb import Expectativas
import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime, timedelta

# Crie um calendário de mercado para a B3
calendario_b3 = mcal.get_calendar("BMF")


# Instancia a classe
em = Expectativas()

# End point
ep = em.get_endpoint("ExpectativasMercadoAnuais")




indicadores = [
    "IPCA",
    "PIB Total",
    "Câmbio",
    "Selic",
    "IGP-M",
    "IPCA Administrados",
    "Conta corrente",
    "Balança comercial",
    "Investimento direto no país",
    "Dívida líquida do setor público",
    "Resultado primário",
    "Resultado nominal",
]

ano_atual = datetime.now().year

# Subtrai um ano usando timedelta
ano_inicio = 2023


anos = [2024, 2025, 2026, 2027]
dados = []
for i in indicadores:
    for ano in anos:
        # Dados do df
        df = (
            ep.query()
            .filter(ep.Indicador == i, ep.DataReferencia == ano)
            .filter(ep.Data >= "2023-01-01")
            .filter(ep.baseCalculo == "0")
            .select(ep.Indicador, ep.Data, ep.Media, ep.Mediana, ep.DataReferencia)
            .collect()
        )

        # Formata a coluna de Data para formato datetime
        df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d")
        df = df.sort_values(by=["Data"], ascending=True)

        # Use o método schedule() para obter o calendário de negociação da B3 para o ano desejado
        calendario = calendario_b3.schedule(
            start_date=f"{ano_inicio}-01-01", end_date=f"{ano_atual}-12-31"
        )

        # Encontrar a data da sexta-feira anterior
        # Obtenha a data atual
        hoje = datetime.now()

        # Calcule a diferença de dias para voltar para a última sexta-feira
        dias_para_subtrair = (
            hoje.weekday() - 4
        ) % 7  # 4 é o código para sexta-feira na biblioteca datetime

        # Subtraia a diferença de dias da data atual
        ultima_sexta_feira = hoje - timedelta(days=dias_para_subtrair)

        # Encontre a data mais recente no calendário de negociação da B3
        # Encontre o último dia útil antes da última sexta-feira
        dt_lp = calendario_b3.valid_days(
            start_date=f"{ano_inicio}-01-01", end_date=ultima_sexta_feira
        )[-1]
        dt_lp = dt_lp.strftime("%Y-%m-%d")

        # Encontrar a data de uma semana atrás
        # Subtrai uma semana usando timedelta
        uma_semana_atras = ultima_sexta_feira - timedelta(days=7)
        # Encontre o último dia útil há uma semana atrás
        dt_1w = calendario_b3.valid_days(
            start_date=f"{ano_inicio}-01-01", end_date=uma_semana_atras
        )[-1]
        dt_1w = dt_1w.strftime("%Y-%m-%d")

        # Encontrar a data de quatro semanas atrás
        # Subtrai 4 semanas usando timedelta
        quatro_semanas_atras = ultima_sexta_feira - timedelta(weeks=4)
        # Encontre o último dia útil há quatro semanas atrás
        dt_4w = calendario_b3.valid_days(
            start_date=f"{ano_inicio}-01-01", end_date=quatro_semanas_atras
        )[-1]
        dt_4w = dt_4w.strftime("%Y-%m-%d")

        # Com a data encontrada, obtenha a linha correspondente no DataFrame

        linha_proc = df[df["Data"] == dt_lp]
        # Se a linha_proc estiver vazia encerra o loop
        if linha_proc.empty:
            continue
        # Nome do Indicador
        else:
            ind = linha_proc["Indicador"].values[0]

            # Data de Referencia do Indicador
            dt_ref = linha_proc["DataReferencia"].values[0]

            # Última Mediana do Indicador
            df_lst = linha_proc["Mediana"].values[0]

            # Com a data encontrada, obtenha a linha correspondente no DataFrame
            linha_proc_1w = df[df["Data"] == dt_1w]

            # Mediana do Indicador de uma semana atrás
            df_1w = linha_proc_1w["Mediana"].values[0]

            if df_lst > df_1w:
                var_1w = "Subiu"
            elif df_lst < df_1w:
                var_1w = "Caiu"
            else:
                var_1w = "Mantido"

            # Com a data encontrada, obtenha a linha correspondente no DataFrame
            linha_proc_4w = df[df["Data"] == dt_4w]
            # Mediana do Indicador de quatro semanaa atrás
            df_4w = linha_proc_4w["Mediana"].values[0]

            if df_lst > df_4w:
                var_4w = "Subiu"
            elif df_lst < df_4w:
                var_4w = "Caiu"
            else:
                var_4w = "Mantido"

            dados.append(
                [
                    ind,
                    dt_ref,
                    round(df_lst, 2),
                    round(df_1w, 2),
                    var_1w,
                    round(df_4w, 2),
                    var_4w,
                ]
            )


focus = pd.DataFrame(
    dados,
    columns=[
        "Indicador",
        "Data de Referência",
        "Mediana",
        "1 semana atrás",
        "Variação",
        "4 semanas atrás",
        "Variação",
    ],
)

if focus.empty:
    print(f"Ainda não saiu o Boletim Focus - {dt_lp}")
else:
    focus.to_excel("focus.xlsx")
    print(focus)


# ['IPCA-15', 'PIB Agropecuária', 'PIB Indústria', 'PIB Serviços', 'Dívida bruta do governo geral', 'IGP-DI', 'INPC',
# 'IPA-DI', 'IPA-M','IPC-Fipe', 'Produção industrial', 'Taxa de desocupação','PIB Despesa de consumo da administração pública',
# 'PIB Formação Bruta de Capital Fixo','PIB Exportação de bens e serviços', 'PIB Importação de bens e serviços', 'IPCA Livres',
# 'IPCA Serviços','IPCA Bens industrializados', 'IPCA Alimentação no domicílio', 'PIB Despesa de consumo das famílias']
