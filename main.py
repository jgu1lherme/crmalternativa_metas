import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.express as px

# Configurar a página para sempre ser exibida em widescreen
st.set_page_config(layout="wide")


def carregar_planilha_metas(caminho_arquivo, aba=0):
    df = pd.read_excel(caminho_arquivo, sheet_name=aba)
    df.rename(columns={df.columns[0]: "Categoria"}, inplace=True)
    return df

def carregar_feriados():
    df = pd.read_excel("resources/FERIADOS.xlsx", header=None)
    df.columns = ['Data']
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    # Converte para datetime.date
    feriados = df['Data'].dt.date.tolist()
    return feriados

def processar_vendas(
    arquivo_vendas,
    mes_referencia=None,
    vendedor_selecionado=None,
    data_inicial=None,
    data_final=None,
):
    df_vendas = pd.read_excel(arquivo_vendas, dtype={"DAT_CAD": str})
    df_vendas["DAT_CAD"] = pd.to_datetime(df_vendas["DAT_CAD"], errors="coerce")

    if df_vendas["DAT_CAD"].isna().all():
        st.error("⚠️ Erro ao processar as datas. Verifique o formato do arquivo.")
        return 0.0, 0.0

    # Se um intervalo de datas for selecionado, aplicar o filtro
    if data_inicial and data_final:
        df_vendas = df_vendas[
            (df_vendas["DAT_CAD"] >= pd.Timestamp(data_inicial))
            & (df_vendas["DAT_CAD"] <= pd.Timestamp(data_final))
        ]
    elif mes_referencia:
        df_vendas = df_vendas[df_vendas["DAT_CAD"].dt.month == mes_referencia]

    if df_vendas.empty:
        st.warning("⚠️ Nenhuma venda encontrada no período selecionado.")
        return 0.0, 0.0

    if vendedor_selecionado and vendedor_selecionado != "Todos":
        df_vendas = df_vendas[df_vendas["VEN_NOME"] == vendedor_selecionado]

    df_vendas["PED_TOTAL"] = pd.to_numeric(
        df_vendas["PED_TOTAL"], errors="coerce"
    ).fillna(0)

    total_opd = df_vendas[df_vendas["PED_OBS_INT"] == "OPD"]["PED_TOTAL"].sum()
    total_amc = df_vendas[df_vendas["PED_OBS_INT"].isin(["DISTRIBICAO", "DISTRIBUICAO", "DISTRIBUIÇÃO", "LOJA"])]["PED_TOTAL"].sum()

    return float(total_opd), float(total_amc)


def calcular_status(realizado, metas, mes_referencia):
    status = ""
    sobra = realizado
    dias_uteis_restantes = calcular_dias_uteis_restantes(
        mes_referencia
    )  # Calcula os dias úteis restantes
    hoje = datetime.date.today()  # Obtém a data de hoje

    # Lista de meses em português
    meses_portugues = [
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ]
    mes_nome = meses_portugues[mes_referencia - 1]

    for nome_meta, valor_meta in metas.items():
        if sobra >= valor_meta:  # Caso a meta tenha sido atingida ou superada
            diferenca = (
                sobra - valor_meta
            )  # Calcula a diferença entre o realizado e a meta
            status += f"✅ Bateu a {nome_meta} (Meta: R$ {valor_meta:,.2f}) com uma diferença de R$ {diferenca:,.2f}\n"
            sobra -= valor_meta
        else:
            status += f"➡️ Falta R$ {valor_meta - sobra:,.2f} para {nome_meta}\n"
            if dias_uteis_restantes > 0:  # Calcula a venda diária necessária
                venda_diaria = (valor_meta - sobra) / dias_uteis_restantes
                status += f"📅 Considerando hoje, dia {hoje.strftime('%d')} de {mes_nome}, precisamos vender R$ {venda_diaria:,.2f} por dia até o final do mês.\n"
            break
    return status


def comparar_com_metas(planilha_metas, mes_referencia, total_opd, total_amc):
    meses = [
        "jan",
        "fev",
        "mar",
        "abr",
        "mai",
        "jun",
        "jul",
        "ago",
        "set",
        "out",
        "nov",
        "dez",
    ]
    mes_coluna = meses[mes_referencia - 1]

    try:
        meta_opd = planilha_metas.loc[
            planilha_metas["Categoria"] == "META AN OPD", mes_coluna
        ].values[0]
        meta_desaf_opd = planilha_metas.loc[
            planilha_metas["Categoria"] == "META DESAF OPD", mes_coluna
        ].values[0]
        meta_distri = planilha_metas.loc[
            planilha_metas["Categoria"] == "META AN DISTRI", mes_coluna
        ].values[0]
        meta_desaf_distri = planilha_metas.loc[
            planilha_metas["Categoria"] == "META DESAF DISTRI", mes_coluna
        ].values[0]
        super_meta_distri = planilha_metas.loc[
            planilha_metas["Categoria"] == "SUPER META DISTRI", mes_coluna
        ].values[0]

        return {
            "OPD": {
                "Realizado": total_opd,
                "Meta Mensal": meta_opd,
                "Meta Desafio": meta_desaf_opd,
            },
            "AMC": {
                "Realizado": total_amc,
                "Meta Mensal": meta_distri,
                "Meta Desafio": meta_desaf_distri,
                "Super Meta": super_meta_distri,
            },
        }
    except IndexError:
        return {}


# Função para gerar gráficos com Plotly
def gerar_grafico(categoria, dados, titulo):
    df = pd.DataFrame({"Tipo": list(dados.keys()), "Valor": list(dados.values())})
    fig = px.bar(
        df,
        x="Tipo",
        y="Valor",
        color="Tipo",
        color_discrete_sequence=["#313334", "#f35202", "#e93900", "#e02500"],
        title=titulo,
    )
    return fig


# # Função para calcular os dias úteis restantes no mês a partir de hoje (sem contar com o dia atual)
# def calcular_dias_uteis_restantes(mes_referencia, incluir_hoje=False):
#     hoje = datetime.date.today()
#     ano_atual = hoje.year
#     primeiro_dia = datetime.date(ano_atual, mes_referencia, 1)

#     if mes_referencia == 12:
#         ultimo_dia = datetime.date(ano_atual + 1, 1, 1) - datetime.timedelta(days=1)
#     else:
#         ultimo_dia = datetime.date(ano_atual, mes_referencia + 1, 1) - datetime.timedelta(days=1)

#     # Lista de dias do mês de hoje até o final
#     dias_mes = pd.date_range(hoje, ultimo_dia).to_list()

#     # Filtra os dias úteis conforme o parâmetro
#     dias_uteis = [
#         dia.date()
#         for dia in dias_mes
#         if dia.weekday() < 5 and (incluir_hoje or dia.date() > hoje)
#     ]

#     return len(dias_uteis)

def calcular_dias_uteis_restantes(mes_referencia, incluir_hoje=False, feriados=None):
    hoje = datetime.date.today()
    ano = hoje.year
    primeiro_dia = datetime.date(ano, mes_referencia, 1)

    if mes_referencia == 12:
        ultimo_dia = datetime.date(ano + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo_dia = datetime.date(ano, mes_referencia + 1, 1) - datetime.timedelta(days=1)

    dias = pd.date_range(hoje, ultimo_dia).to_list()
    dias_uteis = [
        dia.date() for dia in dias
        if dia.weekday() < 5 and (incluir_hoje or dia.date() > hoje)  # Dias úteis (segunda a sexta)
        and (feriados is None or dia.date() not in feriados)  # Exclui feriados se fornecidos
    ]
    return len(dias_uteis)


def calcular_dias_uteis_passados(mes_referencia, incluir_hoje=False, feriados=None):
    hoje = datetime.date.today()
    ano = hoje.year
    primeiro_dia = datetime.date(ano, mes_referencia, 1)

    dias = pd.date_range(primeiro_dia, hoje).to_list()
    dias_uteis = [
        dia.date() for dia in dias
        if dia.weekday() < 5 and (incluir_hoje or dia.date() < hoje)  # Dias úteis (segunda a sexta)
        and (feriados is None or dia.date() not in feriados)  # Exclui feriados se fornecidos
    ]
    return len(dias_uteis)



# # Função para calcular os dias úteis passados no mês
# def calcular_dias_uteis_passados(mes_referencia, incluir_hoje=False):
#     hoje = datetime.date.today()
#     ano_atual = hoje.year
#     primeiro_dia = datetime.date(ano_atual, mes_referencia, 1)

#     # Lista de todos os dias do mês até hoje
#     dias_mes = pd.date_range(primeiro_dia, hoje).to_list()

#     # Filtro de dias úteis
#     dias_uteis = [
#         dia.date() for dia in dias_mes
#         if dia.weekday() < 5 and (incluir_hoje or dia.date() < hoje)
#     ]

#     return len(dias_uteis)


st.title("📊 Comparação de Metas e Vendas")

caminho_metas = "resources/META.xlsx"

uploaded_file = st.file_uploader("📂 Envie a planilha de vendas (1362)", type=["xlsx"])

# Carrega os feriados
feriados = carregar_feriados()

# Opção para escolher entre "Mês" ou "Período Personalizado"
filtro_tipo = st.radio("🔍 Escolha o tipo de filtro:", ["Mês", "Período Personalizado"])

if filtro_tipo == "Mês":
    # Se a escolha for "Mês", mostra apenas o seletor de meses
    mes = st.selectbox(
        "📅 Escolha o mês de referência",
        range(1, 13),
        format_func=lambda x: [
            "janeiro",
            "fevereiro",
            "março",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "dezembro",
        ][x - 1],
    )
    data_inicial, data_final = None, None  # Garante que não use o período

else:
    # Se a escolha for "Período Personalizado", mostra o seletor de datas
    data_intervalo = st.date_input(
        "📅 Selecione o período",
        value=[datetime.date.today().replace(day=1), datetime.date.today()],
    )

    if len(data_intervalo) != 2:
        st.error("⚠️ Selecione uma data inicial e uma data final!")
    else:
        data_inicial, data_final = data_intervalo
        if data_inicial > data_final:
            st.error("⚠️ A data inicial não pode ser maior que a data final!")

    mes = None  # Garante que o filtro por mês não será usado


if uploaded_file:
    df_vendas = pd.read_excel(uploaded_file)
    vendedores = df_vendas["VEN_NOME"].dropna().unique()
    vendedor_selecionado = st.selectbox(
        "👤 Selecione um vendedor", ["Todos"] + list(vendedores)
    )

# -------------------------------------------------------------------------

    # DIVISÃO DE METAS POR VENDEDOR/USUARIO DO SIG2000 RELACIONANDO O MESMO A ALGUMA ABA DA PLANILHA
    rose_loja = ["ROSESILVESTRE"]
    robson_loja = ["ROBSON"]
    # vendedores_loja = ["ROBSON"]
    # danilima = ["DANILIMA"]

    # SE O VENDEDOR "TODOS" FOR SELECIONADO, A "META GERAL" VAI SER IMPOSTA
    if vendedor_selecionado == "Todos":
        aba_meta = "GERAL"

    # elif vendedor_selecionado in vendedores_loja:
        # aba_meta = "LOJA"

    # AO SELECIONAR A "ROSE" OU O "ROBSON", CADA UM TEM SUA "ABA NA PLANILHA" COM SUAS METAS
    elif vendedor_selecionado in rose_loja:
        aba_meta = "ROSE"
    elif vendedor_selecionado in robson_loja:
        aba_meta = "ROBSON"

    # SE O "VENDEDOR" NAO ESTIVER ACIMA, A "ABA GERAL" SERA LIDA E USADA PARA COMPARAÇÃO DE METAS
    else:
        aba_meta = "GERAL"  # Por enquanto, os outros usam a aba GERAL

    # Carrega a planilha de metas com a aba correta
    planilha_metas = carregar_planilha_metas(caminho_metas, aba=aba_meta)

# -----------------------------------------------------------------------------------

if st.button("🔄 Processar Dados"):
    with st.spinner("🔄 Processando..."):
        planilha_metas = carregar_planilha_metas(caminho_metas, aba=aba_meta)

        total_opd, total_amc = processar_vendas(
            uploaded_file,
            (
                mes if not (data_inicial and data_final) else None
            ),  # Usa mês só se datas personalizadas não forem escolhidas
            vendedor_selecionado if vendedor_selecionado != "Todos" else None,
            data_inicial,
            data_final,
        )

        comparacao = comparar_com_metas(planilha_metas, mes, total_opd, total_amc)

        if comparacao:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f"""
                    <div style='background-color:#f35202; padding:10px; border-radius:10px; text-align:center;'>
                        <h4 style='color:#ffff;'>📈 Vendas OPD: R$ {total_opd:,.2f}</h4>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    f"""
                    <div style='background-color:#f35202; padding:10px; border-radius:10px; text-align:center;'>
                        <h4 style='color:#ffff;'>📊 Vendas Distribuição: R$ {total_amc:,.2f}</h4>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col1:
                st.plotly_chart(
                    gerar_grafico("OPD", comparacao["OPD"], "Relação de OPD"),
                    use_container_width=True,
                )
            with col2:
                st.plotly_chart(
                    gerar_grafico("AMC", comparacao["AMC"], "Relação de Distribuição"),
                    use_container_width=True,
                )

# ----------------------------------------------------------------------------------------------

            # Centralizando o título na página
            st.markdown(
                "<h2 style='text-align: center;'>📢 Status das Metas</h2>",
                unsafe_allow_html=True
            )

            # Divide visualmente o conteúdo em duas colunas
            col1, col2 = st.columns(2)

            # ---------- Cálculo dos dias úteis ----------
            dias_uteis_passados = calcular_dias_uteis_passados(mes, incluir_hoje=False, feriados=feriados)
            dias_uteis_restantes = calcular_dias_uteis_restantes(mes, incluir_hoje=True, feriados=feriados)

            dias_uteis_totais = dias_uteis_passados + dias_uteis_restantes

            # Evita divisão por zero
            if dias_uteis_passados == 0:
                dias_uteis_passados = 1
            if dias_uteis_restantes == 0:
                dias_uteis_restantes = 1

            # ---------- Função auxiliar para formatar valores ----------
            def format_valor(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # ---------- Função para calcular tendência ----------
            def calcular_tendencia(realizado, dias_passados, dias_futuros):
                media_diaria = realizado / dias_passados
                tendencia_total = realizado + (media_diaria * dias_futuros)
                return tendencia_total, media_diaria

            # ---------- Geração de cards de KPI (st.metric) ----------
            # def exibir_metricas(coluna, titulo, metas, realizado):
            #     with coluna:
            #         st.markdown(
            #             f"<div style='text-align: center; font-size: 25px; font-weight: bold; margin-bottom: -10px;'>{titulo}</div>",
            #             unsafe_allow_html=True
            #         )
            #         tendencia, media_diaria = calcular_tendencia(realizado, dias_uteis_passados, dias_uteis_restantes)

            #         for nome_meta, valor_meta in metas.items():
            #             necessario = max(0, (valor_meta - realizado) / dias_uteis_restantes)
            #             delta_color = "inverse" if tendencia >= valor_meta else "normal"
            #             st.metric(
            #                 label=f"🎯 {nome_meta}",
            #                 value=format_valor(valor_meta),
            #                 delta=f"Nec/dia: {format_valor(necessario)}",
            #                 delta_color=delta_color
            #             )

            #         st.metric(
            #             "📈 Tendência",
            #             format_valor(tendencia),
            #             delta=f"Média: {format_valor(media_diaria)}"
            #         )

            def exibir_metricas(coluna, titulo, metas, realizado):
                with coluna:
                    st.markdown(
                        f"<div style='text-align: center; font-size: 25px; font-weight: bold; margin-bottom: 15px;'>{titulo}</div>",
                        unsafe_allow_html=True
                    )

                    tendencia, media_diaria = calcular_tendencia(realizado, dias_uteis_passados, dias_uteis_restantes)

                    for nome_meta, valor_meta in metas.items():
                        necessario = max(0, (valor_meta - realizado) / dias_uteis_restantes)
                        delta_color = "inverse" if tendencia >= valor_meta else "normal"

                        # Criar duas colunas lado a lado
                        col1, col2 = st.columns([2, 3])  # Ajuste a proporção como quiser

                        with col1:
                            st.metric(
                                label=f"🎯 {nome_meta}",
                                value=format_valor(valor_meta),
                                delta=f"Nec/dia: {format_valor(necessario)}",
                                delta_color=delta_color
                            )

                            st.metric(
                                label="📈 Tendência (estimativa final)",
                                value=format_valor(tendencia),
                                delta=f"Média diária: {format_valor(media_diaria)}"
                            )

                        with col2:
                            diferenca = tendencia - valor_meta
                            percentual = (diferenca / valor_meta) * 100

                            if diferenca >= 0:
                                texto = f"""
                                <div style="background-color:#262730; padding:16px; border-radius:12px; 
                                            box-shadow:0 2px 6px rgba(0,0,0,0.1); border-left:6px solid #28a745;">
                                    <div style="font-size:16px; font-weight:bold;">📈 Tendência positiva para <u>{nome_meta}</u></div>
                                    <div style="font-size:22px; font-weight:bold; color:#28a745; margin-top:6px;">
                                        +{format_valor(diferenca)} (+{percentual:.1f}%)
                                    </div>
                                    <div style="font-size:14px; color:#555;">Você vai ultrapassar a meta nesse ritmo</div>
                                </div>
                                """
                            else:
                                texto = f"""
                                <div style="background-color:#262730; padding:16px; border-radius:12px; 
                                            box-shadow:0 2px 6px rgba(0,0,0,0.1); border-left:6px solid #dc3545;">
                                    <div style="font-size:16px; font-weight:bold;">📉 Risco de não atingir <u>{nome_meta}</u></div>
                                    <div style="font-size:22px; font-weight:bold; color:#dc3545; margin-top:6px;">
                                        -{format_valor(abs(diferenca))} (-{abs(percentual):.1f}%)
                                    </div>
                                    <div style="font-size:14px; color:#555;">Se continuar assim, vai faltar esse valor</div>
                                </div>
                                """
                            st.markdown(texto, unsafe_allow_html=True)


# ----------------------------- Dados --------------------------------------------------------------------

            # OPD (filtra apenas metas com valor > 0)
            metas_opd = {
                nome: valor for nome, valor in comparacao["OPD"].items()
                if nome != "Realizado" and valor > 0
            }
            realizado_opd = comparacao["OPD"]["Realizado"]

            # Distribuição (filtra apenas metas com valor > 0)
            metas_amc = {
                nome: valor for nome, valor in comparacao["AMC"].items()
                if nome != "Realizado" and valor > 0
            }
            realizado_amc = comparacao["AMC"]["Realizado"]


# ------------------------------- Exibição -------------------------------------------------------------

            exibir_metricas(col1, "📦 OPD", metas_opd, realizado_opd)
            exibir_metricas(col2, "🚚 Distribuição", metas_amc, realizado_amc)

        else:
            st.error("❌ Não foi possível comparar com as metas. Verifique os dados.")
else:
    st.info("📂 Por favor, envie a planilha de vendas e selecione o mês de referência.")
