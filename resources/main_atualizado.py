import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.express as px

# Configurar a página para sempre ser exibida em widescreen
st.set_page_config(layout="wide")

# --- FUNÇÕES EXISTENTES (Com pequenas adaptações) ---

def carregar_planilha_metas(caminho_arquivo, aba=0):
    df = pd.read_excel(caminho_arquivo, sheet_name=aba)
    df.rename(columns={df.columns[0]: "Categoria"}, inplace=True)
    return df

def carregar_feriados():
    try:
        df = pd.read_excel("resources/FERIADOS.xlsx", header=None)
        df.columns = ['Data']
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        feriados = df['Data'].dt.date.tolist()
        return feriados
    except FileNotFoundError:
        st.warning("⚠️ Arquivo 'FERIADOS.xlsx' não encontrado. Dias úteis serão calculados sem feriados.")
        return []

# --- NOVA FUNÇÃO PARA FILTRAR VENDAS ---
def filtrar_vendas(
    arquivo_vendas,
    mes_referencia=None,
    vendedor_selecionado=None,
    data_inicial=None,
    data_final=None,
    com_cdp=False
):
    try:
        df_vendas = pd.read_excel(arquivo_vendas, dtype={"DAT_CAD": str})
    except FileNotFoundError:
        st.error(f"❌ Erro: Arquivo '{arquivo_vendas}' não encontrado. Verifique o caminho.")
        return None

    df_vendas["DAT_CAD"] = pd.to_datetime(df_vendas["DAT_CAD"], errors="coerce")

    if df_vendas["DAT_CAD"].isna().all():
        st.error("⚠️ Erro ao processar as datas. Verifique o formato no arquivo de vendas.")
        return None

    df_vendas["CLI_RAZ"] = df_vendas["CLI_RAZ"].str.strip()
    df_vendas["PED_OBS_INT"] = df_vendas["PED_OBS_INT"].str.strip()
    df_vendas["PED_TOTAL"] = pd.to_numeric(df_vendas["PED_TOTAL"], errors="coerce").fillna(0)

    # Convertendo para apenas data (sem hora) para consistência nos filtros
    df_vendas["DAT_CAD_DATE"] = df_vendas["DAT_CAD"].dt.date

    # Aplicar filtro de data
    if data_inicial and data_final:
        data_inicial_dt = pd.to_datetime(data_inicial).date()
        data_final_dt = pd.to_datetime(data_final).date()
        df_vendas = df_vendas[
            (df_vendas["DAT_CAD_DATE"] >= data_inicial_dt) &
            (df_vendas["DAT_CAD_DATE"] <= data_final_dt)
        ]
    elif mes_referencia:
        df_vendas = df_vendas[df_vendas["DAT_CAD"].dt.month == mes_referencia]
        # Adicionalmente, filtrar pelo ano atual se o mês for selecionado
        ano_atual = datetime.date.today().year
        df_vendas = df_vendas[df_vendas["DAT_CAD"].dt.year == ano_atual]


    if df_vendas.empty:
        st.warning("⚠️ Nenhuma venda encontrada no período selecionado.")
        return pd.DataFrame() # Retorna DF vazio para evitar erros

    # Filtro de Vendedor
    if vendedor_selecionado and vendedor_selecionado != "Todos":
        df_vendas = df_vendas[df_vendas["VEN_NOME"] == vendedor_selecionado]

    # Lista dos nomes da Casa do Pedreiro
    nomes_cdp = [
        "DO PEDREIRO DO LITORAL COMERC DE MATERIAIS DE CONSTRUCAO LTD",
        "DO PEDREIRO DO LITORAL COMERCIO DE MATERIAIS DE CONSTRUCAO",
    ]

    # Filtro Casa do Pedreiro
    if not com_cdp:
        df_vendas = df_vendas[~df_vendas["CLI_RAZ"].isin(nomes_cdp)]

    return df_vendas


# --- FUNÇÃO PROCESSAR_VENDAS (Agora usa filtrar_vendas) ---
def processar_vendas(df_vendas_filtrado):
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        return 0.0, 0.0

    # Filtro base para OPD e faturado
    filtro_opd = (df_vendas_filtrado["PED_OBS_INT"] == "OPD") & (df_vendas_filtrado["PED_STATUS"] == "F")
    total_opd = df_vendas_filtrado[filtro_opd]["PED_TOTAL"].sum()

    # Soma dos valores para AMC
    total_amc = df_vendas_filtrado[df_vendas_filtrado["PED_OBS_INT"].isin([ "DISTRIBICAO", "DISTRIBUICAO", "DISTRIBUIÇÃO", "LOJA"])]["PED_TOTAL"].sum()

    return float(total_opd), float(total_amc)

# --- FUNÇÕES EXISTENTES (calcular_status, comparar_com_metas, gerar_grafico, calcular_dias_uteis) ---
# (Mantidas como no seu código original, mas garantindo que `calcular_dias_uteis_restantes` e `calcular_dias_uteis_passados`
#  recebam o mês corretamente)
def calcular_status(realizado, metas, mes_referencia, feriados):
    status = ""
    sobra = realizado
    dias_uteis_restantes = calcular_dias_uteis_restantes(
        mes_referencia, feriados=feriados, incluir_hoje=True # Inclui hoje no cálculo
    )
    hoje = datetime.date.today()

    meses_portugues = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    mes_nome = meses_portugues[mes_referencia - 1]

    for nome_meta, valor_meta in metas.items():
        if sobra >= valor_meta:
            diferenca = sobra - valor_meta
            status += f"✅ Bateu a {nome_meta} (Meta: R$ {valor_meta:,.2f}) com uma diferença de R$ {diferenca:,.2f}\n"
            sobra -= valor_meta
        else:
            status += f"➡️ Falta R$ {valor_meta - sobra:,.2f} para {nome_meta}\n"
            if dias_uteis_restantes > 0:
                venda_diaria = (valor_meta - sobra) / dias_uteis_restantes
                status += f"📅 Considerando hoje ({hoje.strftime('%d/%m')}), precisamos vender R$ {venda_diaria:,.2f} por dia.\n"
            else:
                 status += f"📅 Não há mais dias úteis neste mês para vender.\n"
            break
    return status

def comparar_com_metas(planilha_metas, mes_referencia, total_opd, total_amc):
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    mes_coluna = meses[mes_referencia - 1]

    try:
        meta_opd = float(planilha_metas.loc[planilha_metas["Categoria"] == "META AN OPD", mes_coluna].values[0])
        meta_desaf_opd = float(planilha_metas.loc[planilha_metas["Categoria"] == "META DESAF OPD", mes_coluna].values[0])
        meta_distri = float(planilha_metas.loc[planilha_metas["Categoria"] == "META AN DISTRI", mes_coluna].values[0])
        meta_desaf_distri = float(planilha_metas.loc[planilha_metas["Categoria"] == "META DESAF DISTRI", mes_coluna].values[0])
        super_meta_distri = float(planilha_metas.loc[planilha_metas["Categoria"] == "SUPER META DISTRI", mes_coluna].values[0])

        return {
            "OPD": {"Realizado": total_opd, "Meta Mensal": meta_opd, "Meta Desafio": meta_desaf_opd},
            "AMC": {"Realizado": total_amc, "Meta Mensal": meta_distri, "Meta Desafio": meta_desaf_distri, "Super Meta": super_meta_distri},
        }
    except (IndexError, KeyError) as e:
        st.error(f"❌ Erro ao ler metas para o mês '{mes_coluna}' na aba selecionada. Verifique a planilha. Detalhe: {e}")
        return {}


def gerar_grafico(categoria, dados, titulo):
    df = pd.DataFrame({"Tipo": list(dados.keys()), "Valor": list(dados.values())})
    fig = px.bar(
        df, x="Tipo", y="Valor", color="Tipo",
        color_discrete_sequence=["#313334", "#f35202", "#e93900", "#e02500"],
        title=titulo, text_auto=True # Mostra valores nas barras
    )
    fig.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valor (R$)")
    return fig


def calcular_dias_uteis_restantes(mes_referencia, incluir_hoje=True, feriados=None):
    hoje = datetime.date.today()
    ano = hoje.year

    # Se o mês de referência já passou, não há dias restantes
    if ano > hoje.year or (ano == hoje.year and mes_referencia < hoje.month):
        return 0

    # Se o mês de referência for o atual, começa de hoje
    if mes_referencia == hoje.month:
        data_inicio = hoje
    # Se for um mês futuro, começa do primeiro dia desse mês
    else:
        data_inicio = datetime.date(ano, mes_referencia, 1)

    # Calcula o último dia do mês de referência
    if mes_referencia == 12:
        ultimo_dia = datetime.date(ano, 12, 31)
    else:
        ultimo_dia = datetime.date(ano, mes_referencia + 1, 1) - datetime.timedelta(days=1)

    # Garante que não calcule dias que já passaram se a data de início for hoje
    dias = pd.date_range(data_inicio, ultimo_dia).to_list()
    feriados = feriados or []

    dias_uteis_count = 0
    for dia in dias:
        dia_date = dia.date()
        if dia.weekday() < 5 and dia_date not in feriados: # Segunda a Sexta e não feriado
            if incluir_hoje:
                 dias_uteis_count += 1
            elif dia_date > hoje:
                 dias_uteis_count += 1

    return dias_uteis_count


def calcular_dias_uteis_passados(mes_referencia, incluir_hoje=False, feriados=None):
    hoje = datetime.date.today()
    ano = hoje.year
    feriados = feriados or []

    primeiro_dia = datetime.date(ano, mes_referencia, 1)
    # Define o dia final como hoje ou o último dia do mês, o que vier primeiro
    dia_final = min(hoje, datetime.date(ano, mes_referencia + 1, 1) - datetime.timedelta(days=1) if mes_referencia < 12 else datetime.date(ano, 12, 31))


    dias = pd.date_range(primeiro_dia, dia_final).to_list()
    dias_uteis_count = 0
    for dia in dias:
        dia_date = dia.date()
        if dia.weekday() < 5 and dia_date not in feriados: # Segunda a Sexta e não feriado
            if incluir_hoje or dia_date < hoje:
                dias_uteis_count += 1

    return dias_uteis_count


# --- NOVAS FUNÇÕES PARA TABELAS ---

def gerar_tabela_geral(df_vendas_filtrado):
    """Gera uma tabela com o total de vendas por vendedor."""
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        st.info("Nenhuma venda encontrada para gerar o relatório geral.")
        return pd.DataFrame()

    df = df_vendas_filtrado.copy()

    # Classificar vendas
    df['Tipo Venda'] = np.where(
        (df['PED_OBS_INT'] == 'OPD') & (df['PED_STATUS'] == 'F'), 'OPD',
        np.where(df['PED_OBS_INT'].isin(['DISTRIBICAO', 'DISTRIBUICAO', 'DISTRIBUIÇÃO', 'LOJA']), 'Distribuição', 'Outros')
    )

    # Filtrar apenas OPD e Distribuição válidos
    df_validos = df[df['Tipo Venda'].isin(['OPD', 'Distribuição'])]

    # Pivotar para ter colunas OPD e Distribuição
    tabela = pd.pivot_table(
        df_validos,
        values='PED_TOTAL',
        index='VEN_NOME',
        columns='Tipo Venda',
        aggfunc=np.sum,
        fill_value=0
    )

    # Garantir que ambas as colunas existam
    if 'OPD' not in tabela.columns:
        tabela['OPD'] = 0
    if 'Distribuição' not in tabela.columns:
        tabela['Distribuição'] = 0

    # Calcular total e formatar
    tabela['Total Vendedor'] = tabela['OPD'] + tabela['Distribuição']
    tabela = tabela.sort_values(by='Total Vendedor', ascending=False)

    # Adicionar linha de Total Geral
    total_geral = tabela.sum().to_frame().T
    total_geral.index = ['**TOTAL GERAL**']
    tabela = pd.concat([tabela, total_geral])

    # Formatar como moeda
    for col in ['OPD', 'Distribuição', 'Total Vendedor']:
        tabela[col] = tabela[col].apply(lambda x: f"R$ {x:,.2f}")

    return tabela.reset_index().rename(columns={'VEN_NOME': 'Vendedor'})


def gerar_tabela_vendedor(df_vendas_filtrado):
    """Gera uma tabela detalhada das vendas de um vendedor."""
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        st.info("Nenhuma venda encontrada para este vendedor no período.")
        return pd.DataFrame()

    df = df_vendas_filtrado.copy()

    # Classificar vendas
    df['Tipo Venda'] = np.where(
        (df['PED_OBS_INT'] == 'OPD') & (df['PED_STATUS'] == 'F'), 'OPD',
        np.where(df['PED_OBS_INT'].isin(['DISTRIBICAO', 'DISTRIBUICAO', 'DISTRIBUIÇÃO', 'LOJA']), 'Distribuição', 'Outros')
    )

    # Filtrar apenas OPD e Distribuição válidos
    df = df[df['Tipo Venda'].isin(['OPD', 'Distribuição'])]

    # Selecionar e renomear colunas, MANTENDO 'DAT_CAD' como datetime
    tabela = df[[
        'DAT_CAD',
        'VEN_NOME',
        'CLI_RAZ',
        'PED_TOTAL',
        'Tipo Venda'
    ]].copy()

    tabela.rename(columns={
        # 'DAT_CAD': 'Data', # AINDA NÃO RENOMEIA/FORMATA
        'VEN_NOME': 'Vendedor',
        'CLI_RAZ': 'Cliente',
        'PED_TOTAL': 'Valor',
    }, inplace=True)

    # *** 1. Ordenar PELA COLUNA DATETIME ORIGINAL ***
    tabela = tabela.sort_values(by='DAT_CAD', ascending=True)

    # *** 2. AGORA, formatar data e valor ***
    tabela['Data'] = tabela['DAT_CAD'].dt.strftime('%d/%m/%Y')
    tabela['Valor'] = tabela['Valor'].apply(lambda x: f"R$ {x:,.2f}")

    # *** 3. Selecionar e reordenar as colunas FINAIS ***
    tabela_final = tabela[[
        'Data',
        'Vendedor',
        'Cliente',
        'Valor',
        'Tipo Venda'
    ]]

    return tabela_final # Retorna a tabela final formatada e ordenada

# --- INTERFACE STREAMLIT ---

st.sidebar.title("📊 Navegação")
pagina_selecionada = st.sidebar.radio(
    "Escolha a visualização:",
    ["Painel Principal", "Relatórios Detalhados"]
)

st.title(f"📈 {pagina_selecionada}")

caminho_metas = "resources/META.xlsx"
caminho_vendas_padrao = "resources/VENDAS.xlsx"
uploaded_file = caminho_vendas_padrao

# Carrega os feriados
feriados = carregar_feriados()

# --- Filtros (Comuns a ambas as páginas) ---
st.sidebar.header("Filtros")
filtro_tipo = st.sidebar.radio("🔍 Tipo de filtro:", ["Mês", "Período Personalizado"])

mes_selecionado = None
data_inicial, data_final = None, None

if filtro_tipo == "Mês":
    mes_selecionado = st.sidebar.selectbox(
        "📅 Mês de referência", range(1, 13),
        format_func=lambda x: ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][x - 1],
        index=datetime.date.today().month - 1 # Padrão para o mês atual
    )
    # Define data_inicial e data_final para o mês selecionado
    ano_atual = datetime.date.today().year
    data_inicial = datetime.date(ano_atual, mes_selecionado, 1)
    if mes_selecionado == 12:
        data_final = datetime.date(ano_atual, 12, 31)
    else:
        data_final = datetime.date(ano_atual, mes_selecionado + 1, 1) - datetime.timedelta(days=1)
    st.sidebar.info(f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}")

else: # Período Personalizado
    data_intervalo = st.sidebar.date_input(
        "📅 Selecione o período",
        value=[datetime.date.today().replace(day=1), datetime.date.today()],
    )
    if len(data_intervalo) == 2:
        data_inicial, data_final = data_intervalo
        if data_inicial > data_final:
            st.sidebar.error("⚠️ A data inicial não pode ser maior que a data final!")
            st.stop() # Interrompe a execução se as datas forem inválidas
        # Determina o mês de referência (usado para metas) com base na data final
        mes_selecionado = data_final.month
    else:
        st.sidebar.error("⚠️ Selecione uma data inicial e uma data final!")
        st.stop()

# Carregar vendedores (precisa acontecer antes de selecionar)
try:
    df_vendas_bruto = pd.read_excel(uploaded_file)
    vendedores = ["Todos"] + sorted(list(df_vendas_bruto["VEN_NOME"].dropna().unique()))
    vendedor_selecionado = st.sidebar.selectbox("👤 Vendedor", vendedores)
except FileNotFoundError:
    st.error(f"❌ Erro: Arquivo '{uploaded_file}' não encontrado. Verifique o caminho.")
    st.stop()


# Filtro CDP
com_cdp = st.sidebar.checkbox("Incluir vendas da Casa do Pedreiro", value=True)

# --- Seleção da Aba de Metas ---
rose_loja = ["ROSESILVESTRE"]
robson_loja = ["ROBSON"]
danilima_d = ["DANILIMA"]
renato_d = ["JOSE RENATO MAULER"]

if vendedor_selecionado == "Todos":
    aba_meta = "GERAL"
elif vendedor_selecionado in rose_loja:
    aba_meta = "ROSE"
elif vendedor_selecionado in robson_loja:
    aba_meta = "ROBSON"
elif vendedor_selecionado in danilima_d:
    aba_meta = "DANILIMA"
elif vendedor_selecionado in renato_d:
    aba_meta = "RENATO"
else:
    aba_meta = "GERAL"

# --- Lógica de Exibição ---

# Botão para processar, agora na barra lateral para ficar sempre visível
if st.sidebar.button("🔄 Processar Dados"):
    with st.spinner("🔄 Processando..."):
        # 1. Filtrar vendas com base nos seletores
        df_filtrado = filtrar_vendas(
            uploaded_file,
            mes_selecionado if filtro_tipo == "Mês" else None,
            vendedor_selecionado,
            data_inicial,
            data_final,
            com_cdp
        )

        # 2. Carregar Metas
        try:
            planilha_metas = carregar_planilha_metas(caminho_metas, aba=aba_meta)
        except FileNotFoundError:
            st.error(f"❌ Erro: Arquivo de Metas '{caminho_metas}' não encontrado.")
            planilha_metas = None
        except Exception as e:
            st.error(f"❌ Erro ao carregar a aba '{aba_meta}' da planilha de metas: {e}")
            planilha_metas = None


        # 3. Processar Vendas (somente se houver dados filtrados)
        if df_filtrado is not None and not df_filtrado.empty:
            total_opd, total_amc = processar_vendas(df_filtrado)
        else:
            total_opd, total_amc = 0.0, 0.0

        # 4. Comparar com Metas (somente se houver metas e mês)
        comparacao = {}
        if planilha_metas is not None and mes_selecionado:
             comparacao = comparar_com_metas(planilha_metas, mes_selecionado, total_opd, total_amc)

        # 5. Armazenar os resultados no estado da sessão para usar nas páginas
        st.session_state['df_filtrado'] = df_filtrado
        st.session_state['total_opd'] = total_opd
        st.session_state['total_amc'] = total_amc
        st.session_state['comparacao'] = comparacao
        st.session_state['mes_selecionado'] = mes_selecionado
        st.session_state['feriados'] = feriados
        st.session_state['vendedor_selecionado'] = vendedor_selecionado


# --- Exibição da Página Selecionada ---

if 'df_filtrado' not in st.session_state:
    st.info("📂 Selecione os filtros na barra lateral e clique em 'Processar Dados'.")
else:
    # Recupera os dados processados da sessão
    df_filtrado = st.session_state['df_filtrado']
    total_opd = st.session_state['total_opd']
    total_amc = st.session_state['total_amc']
    comparacao = st.session_state['comparacao']
    mes = st.session_state['mes_selecionado']
    feriados = st.session_state['feriados']
    vendedor_selecionado = st.session_state['vendedor_selecionado']

    # ==================================================================
    #                      PÁGINA: PAINEL PRINCIPAL
    # ==================================================================
    if pagina_selecionada == "Painel Principal":
        if df_filtrado is None or df_filtrado.empty:
            st.warning("Nenhum dado para exibir no Painel Principal com os filtros atuais.")
        elif not comparacao:
             st.warning("Metas não carregadas. O painel será exibido sem comparações.")
             # Mesmo sem metas, podemos mostrar os totais e talvez os gráficos básicos
             col1, col2 = st.columns(2)
             with col1:
                 st.metric("📈 Vendas OPD", f"R$ {total_opd:,.2f}")
             with col2:
                 st.metric("📊 Vendas Distribuição", f"R$ {total_amc:,.2f}")

        else:
            # --- SEU CÓDIGO DO PAINEL PRINCIPAL (Cálculos de Tendência, Gráficos, Métricas) ---
            dias_uteis_passados = calcular_dias_uteis_passados(mes, incluir_hoje=False, feriados=feriados)
            dias_uteis_restantes = calcular_dias_uteis_restantes(mes, incluir_hoje=True, feriados=feriados)
            dias_uteis_passados = max(1, dias_uteis_passados) # Evita divisão por zero
            dias_uteis_restantes = max(1, dias_uteis_restantes) # Evita divisão por zero

            def format_valor(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            def calcular_tendencia(realizado, dias_passados, dias_futuros):
                media_diaria = realizado / dias_passados
                tendencia_total = realizado + (media_diaria * dias_futuros)
                return tendencia_total, media_diaria

            # Exibição "Todos"
            if vendedor_selecionado == "Todos":
                soma_total = total_opd + total_amc
                realizado_geral = soma_total
                meta_geral = comparacao.get("OPD", {}).get("Meta Mensal", 0) + comparacao.get("AMC", {}).get("Meta Mensal", 0)
                meta_desafio = comparacao.get("OPD", {}).get("Meta Desafio", 0) + comparacao.get("AMC", {}).get("Meta Desafio", 0)
                super_meta = comparacao.get("AMC", {}).get("Super Meta", 0) # Assumindo que super meta é só AMC

                def gerar_bloco_meta(titulo, meta_valor):
                    tendencia, media_diaria = calcular_tendencia(realizado_geral, dias_uteis_passados, dias_uteis_restantes)
                    necessario_por_dia = max(0, (meta_valor - realizado_geral) / dias_uteis_restantes) if dias_uteis_restantes > 0 else 0
                    html = (
                        f"<div style='background-color:#262730; padding:10px; border-radius:10px; width:33%; text-align:center; margin-bottom:10px;'>"
                        f"<h4 style='color:#ffffff;'>{titulo}: {format_valor(meta_valor)}</h4>"
                        f"<p style='color:#cccccc; margin:4px;'>📈 Tendência: {format_valor(tendencia)}</p>"
                        f"<p style='color:#cccccc; margin:4px;'>📊 Média Diária: {format_valor(media_diaria)}</p>"
                        f"<p style='color:#cccccc; margin:4px;'>📅 Necessário/dia: {format_valor(necessario_por_dia)}</p>"
                        f"</div>"
                    )
                    return html

                bloco_mensal = gerar_bloco_meta("Meta Mensal", meta_geral)
                bloco_desafio = gerar_bloco_meta("Meta Desafio", meta_desafio)
                bloco_super = gerar_bloco_meta("Super Meta", super_meta)

                st.markdown(f"<div style='background-color:#262730; padding:10px; border-radius:10px; text-align:center; margin-top:10px; margin-bottom:10px;'><h4 style='color:#ffffff;'>💰 Total Geral da Empresa: {format_valor(soma_total)}</h4></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='display: flex; justify-content: space-between; gap: 10px; margin-top:0px;'>{bloco_mensal}{bloco_desafio}{bloco_super}</div>", unsafe_allow_html=True)


            # Exibição Gráficos e Títulos (Para todos os casos com dados)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div style='background-color:#f35202; padding:10px; border-radius:10px; text-align:center;'><h4 style='color:#ffff;'>📈 Vendas OPD: R$ {total_opd:,.2f}</h4></div>", unsafe_allow_html=True)
                st.plotly_chart(gerar_grafico("OPD", comparacao["OPD"], "Relação de OPD"), use_container_width=True)
            with col2:
                st.markdown(f"<div style='background-color:#f35202; padding:10px; border-radius:10px; text-align:center;'><h4 style='color:#ffff;'>📊 Vendas Distribuição: R$ {total_amc:,.2f}</h4></div>", unsafe_allow_html=True)
                st.plotly_chart(gerar_grafico("AMC", comparacao["AMC"], "Relação de Distribuição"), use_container_width=True)

            # Exibição Métricas Detalhadas
            st.markdown("<h2 style='text-align: center; margin-top: 30px;'>📢 Status das Metas</h2>", unsafe_allow_html=True)
            col1_m, col2_m = st.columns(2)

            def exibir_metricas(coluna, titulo, metas, realizado):
                 with coluna:
                    st.markdown(f"<div style='text-align: center; font-size: 25px; font-weight: bold; margin-bottom: 15px;'>{titulo}</div>", unsafe_allow_html=True)
                    tendencia, media_diaria = calcular_tendencia(realizado, dias_uteis_passados, dias_uteis_restantes)

                    for nome_meta, valor_meta in metas.items():
                        if nome_meta == "Realizado" or valor_meta <= 0: continue # Pula o realizado e metas zeradas

                        necessario = max(0, (valor_meta - realizado) / dias_uteis_restantes) if dias_uteis_restantes > 0 else 0
                        delta_color = "inverse" if tendencia >= valor_meta else "normal"
                        diferenca = tendencia - valor_meta
                        percentual = (diferenca / valor_meta) * 100 if valor_meta > 0 else 0

                        st.metric(
                            label=f"🎯 {nome_meta}",
                            value=format_valor(valor_meta),
                            delta=f"Nec/dia: {format_valor(necessario)}",
                            delta_color=delta_color
                        )

                        if diferenca >= 0:
                            cor_borda = "#28a745" # Verde
                            sinal = "+"
                            texto_status = f"📈 Tendência positiva para <u>{nome_meta}</u>"
                            texto_rodape = "Você vai ultrapassar a meta nesse ritmo"
                        else:
                            cor_borda = "#dc3545" # Vermelho
                            sinal = "-"
                            texto_status = f"📉 Risco de não atingir <u>{nome_meta}</u>"
                            texto_rodape = "Se continuar assim, vai faltar esse valor"

                        texto_html = f"""
                        <div style="background-color:#262730; padding:16px; border-radius:12px; margin-bottom:15px;
                                    box-shadow:0 2px 6px rgba(0,0,0,0.1); border-left:6px solid {cor_borda};">
                            <div style="font-size:16px; font-weight:bold;">{texto_status}</div>
                            <div style="font-size:22px; font-weight:bold; color:{cor_borda}; margin-top:6px;">
                                {sinal}{format_valor(abs(diferenca))} ({sinal}{abs(percentual):.1f}%)
                            </div>
                            <div style="font-size:14px; color:#cccccc;">{texto_rodape}</div>
                            <div style="font-size:14px; color:#cccccc; margin-top:5px;"><i>Tendência: {format_valor(tendencia)} | Média diária: {format_valor(media_diaria)}</i></div>
                        </div>
                        """
                        st.markdown(texto_html, unsafe_allow_html=True)
                        st.markdown("---") # Linha divisória

            metas_opd = {k: v for k, v in comparacao["OPD"].items() if v > 0}
            metas_amc = {k: v for k, v in comparacao["AMC"].items() if v > 0}
            exibir_metricas(col1_m, "📦 OPD", metas_opd, total_opd)
            exibir_metricas(col2_m, "🚚 Distribuição", metas_amc, total_amc)


    # ==================================================================
    #                    PÁGINA: RELATÓRIOS DETALHADOS
    # ==================================================================
    elif pagina_selecionada == "Relatórios Detalhados":
        if df_filtrado is None or df_filtrado.empty:
            st.warning("Nenhum dado para exibir nos Relatórios com os filtros atuais.")
        else:
            # Se "Todos" estiver selecionado, mostra a tabela geral
            if vendedor_selecionado == "Todos":
                st.subheader("📋 Resumo de Vendas por Vendedor")
                tabela_geral = gerar_tabela_geral(df_filtrado)
                if not tabela_geral.empty:
                    st.dataframe(tabela_geral, use_container_width=True)
                else:
                    st.info("Nenhuma venda OPD ou Distribuição encontrada para o resumo geral.")

            # Se um vendedor específico estiver selecionado, mostra a tabela detalhada
            else:
                st.subheader(f"📋 Detalhe de Vendas - {vendedor_selecionado}")
                tabela_detalhada = gerar_tabela_vendedor(df_filtrado)
                if not tabela_detalhada.empty:
                    st.dataframe(tabela_detalhada, use_container_width=True)
                else:
                    st.info(f"Nenhuma venda OPD ou Distribuição encontrada para {vendedor_selecionado} no período.")
