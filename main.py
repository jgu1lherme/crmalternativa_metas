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


def processar_vendas(arquivo_vendas, vendedor_selecionado=None):
    df_vendas = pd.read_excel(arquivo_vendas)
    df_vendas = df_vendas.dropna(subset=["AL_COD"])

    if vendedor_selecionado:
        df_vendas = df_vendas[df_vendas["VEN_NOME"] == vendedor_selecionado]

    total_opd = df_vendas[df_vendas["AL_COD"] == "OPD"]["PED_TOTAL"].sum()
    total_amc = df_vendas[df_vendas["AL_COD"] == "AMC"]["PED_TOTAL"].sum()

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
                "Meta AN": meta_opd,
                "Meta Desafio": meta_desaf_opd,
            },
            "AMC": {
                "Realizado": total_amc,
                "Meta AN": meta_distri,
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


# Função para calcular os dias úteis restantes no mês a partir de hoje (sem contar com o dia atual)
def calcular_dias_uteis_restantes(mes_referencia):
    ano_atual = datetime.datetime.now().year
    primeiro_dia = datetime.date(ano_atual, mes_referencia, 1)
    if mes_referencia == 12:
        ultimo_dia = datetime.date(ano_atual + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo_dia = datetime.date(
            ano_atual, mes_referencia + 1, 1
        ) - datetime.timedelta(days=1)

    # Verifique a data de hoje, mas não conte o dia atual
    hoje = datetime.date.today()
    if hoje > ultimo_dia:
        return 0

    # Gerar a lista de dias do mês
    dias_mes = pd.date_range(primeiro_dia, ultimo_dia).to_list()

    # Contar os dias úteis (excluindo finais de semana) restantes após hoje
    dias_uteis_restantes = [
        dia.date()
        for dia in dias_mes
        if dia.weekday() < 5
        and dia.date() > hoje  # Verifique que o dia é posterior ao hoje
    ]

    # Depuração
    print(f"Dias úteis restantes (sem contar o hoje): {dias_uteis_restantes}")

    return len(dias_uteis_restantes)


st.title("📊 Comparação de Metas e Vendas")

caminho_metas = "META.xlsx"
planilha_metas = carregar_planilha_metas(caminho_metas)

uploaded_file = st.file_uploader("📂 Envie a planilha de vendas", type=["xlsx"])
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

if uploaded_file:
    df_vendas = pd.read_excel(uploaded_file)
    vendedores = df_vendas["VEN_NOME"].dropna().unique()
    vendedor_selecionado = st.selectbox(
        "👤 Selecione um vendedor", ["Todos"] + list(vendedores)
    )

if st.button("🔄 Processar Dados"):
    with st.spinner("🔄 Processando..."):
        aba_meta = (
            0 if vendedor_selecionado == "Todos" else 1
        )  # 0 para a primeira aba, 1 para a segunda
        planilha_metas = carregar_planilha_metas(caminho_metas, aba=aba_meta)

        total_opd, total_amc = processar_vendas(
            uploaded_file,
            None if vendedor_selecionado == "Todos" else vendedor_selecionado,
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

            # Centralizando o título na página
            st.markdown(
                """
                <div style='text-align: center;'>
                    <h2>📢 Status das Metas</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Criando as duas colunas abaixo do título centralizado
            col1, col2 = st.columns(2)

            # Número de dias úteis restantes no mês
            dias_uteis_restantes = calcular_dias_uteis_restantes(mes)

            # Evitar divisão por zero caso não haja mais dias úteis
            if dias_uteis_restantes == 0:
                dias_uteis_restantes = 1

            # Dados para a coluna OPD (agora com a coluna 'Necessário por Dia')
            data_opd = {
                "Meta": ["Meta AN", "Meta Desafio", "Realizado"],
                "Valor": [
                    comparacao["OPD"]["Meta AN"],
                    comparacao["OPD"]["Meta Desafio"],
                    comparacao["OPD"]["Realizado"],
                ],
                "Necessário por Dia": [
                    max(
                        0,
                        (comparacao["OPD"]["Meta AN"] - comparacao["OPD"]["Realizado"])
                        / dias_uteis_restantes,
                    ),
                    max(
                        0,
                        (
                            comparacao["OPD"]["Meta Desafio"]
                            - comparacao["OPD"]["Realizado"]
                        )
                        / dias_uteis_restantes,
                    ),
                    comparacao["OPD"]["Realizado"] / dias_uteis_restantes,
                ],
            }

            # Dados para a coluna Distribuição (agora com a coluna 'Necessário por Dia')
            data_dist = {
                "Meta": ["Meta AN", "Meta Desafio", "Super Meta", "Realizado"],
                "Valor": [
                    comparacao["AMC"]["Meta AN"],
                    comparacao["AMC"]["Meta Desafio"],
                    comparacao["AMC"].get("Super Meta", 0),
                    comparacao["AMC"]["Realizado"],
                ],
                "Necessário por Dia": [
                    max(
                        0,
                        (comparacao["AMC"]["Meta AN"] - comparacao["AMC"]["Realizado"])
                        / dias_uteis_restantes,
                    ),
                    max(
                        0,
                        (
                            comparacao["AMC"]["Meta Desafio"]
                            - comparacao["AMC"]["Realizado"]
                        )
                        / dias_uteis_restantes,
                    ),
                    max(
                        0,
                        (
                            comparacao["AMC"].get("Super Meta", 0)
                            - comparacao["AMC"]["Realizado"]
                        )
                        / dias_uteis_restantes,
                    ),
                    comparacao["AMC"]["Realizado"] / dias_uteis_restantes,
                ],
            }

            # Convertendo para DataFrame
            df_opd = pd.DataFrame(data_opd)
            df_dist = pd.DataFrame(data_dist)

            # Exibir tabelas nas colunas
            with col1:
                st.markdown(
                    """
                    <div style='text-align: center;'>
                    <h3>OPD</h3>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.table(df_opd)

            with col2:
                st.markdown(
                    """
                    <div style='text-align: center;'>
                    <h3>Distribuição</h3>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.table(df_dist)

        else:
            st.error("❌ Não foi possível comparar com as metas. Verifique os dados.")
else:
    st.info("📂 Por favor, envie a planilha de vendas e selecione o mês de referência.")
