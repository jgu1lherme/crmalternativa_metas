import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.express as px

# Configurar a página para sempre ser exibida em widescreen
st.set_page_config(
    page_title="BI - Nova Alternativa",
    page_icon="assets/logo.png",
    layout="wide"
    )

# --- FUNÇÕES EXISTENTES (Com pequenas adaptações) ---

def carregar_planilha_metas(caminho_arquivo, aba=0):
    df = pd.read_excel(caminho_arquivo, sheet_name=aba)
    df.rename(columns={df.columns[0]: "Categoria"}, inplace=True)
    return df

# --------------------------------------------------------------------------------
# VERSÃO ATUALIZADA DA FUNÇÃO DE PAINEL FINANCEIRO (SIMPLIFICADA)
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# VERSÃO FINAL DA FUNÇÃO DE PAINEL FINANCEIRO (100% BASEADA NO STATUS DA PLANILHA)
# --------------------------------------------------------------------------------
def criar_painel_financeiro_avancado(
    titulo,
    df_filtrado,
    coluna_valor,
    coluna_status,
    coluna_entidade,
    coluna_vencimento,
):
    """
    Cria e exibe um painel financeiro avançado,
    exibindo KPIs de Total, Em Aberto e Pago.
    """

    import streamlit as st

    if df_filtrado.empty:
        st.info(f"Não há dados de '{titulo}' para exibir com os filtros selecionados.")
        return

    # --- 1. CÁLCULO DOS KPIs ---
    valor_total = df_filtrado[coluna_valor].sum()
    valor_pago = df_filtrado[df_filtrado[coluna_status] == 'PAGO'][coluna_valor].sum()
    valor_em_aberto = df_filtrado[df_filtrado[coluna_status] == 'EM ABERTO'][coluna_valor].sum()

    # --- 2. BLOCO DO TÍTULO ---
    st.markdown(f"""
        <div style="
            background-color: #161616;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-top: 10px;
            margin-bottom: 20px;
        ">
            <h3 style="color: #ffffff; margin: 0;">{titulo}</h3>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. BLOCOS DOS KPIs ---
    bloco_total = f"""
        <div style="
            background-color: #f35202;
            padding: 13px;
            border-radius: 10px;
            text-align: center;
            flex: 1;
            min-width: 150px;
        ">
            <h4 style="color: #ffffff; margin: 3px; font-weight: 400;">💰 Valor Total</h4>
            <p style="color: #ffffff; font-size: 1.6rem; margin: 0; font-weight: 700;">
                R$ {valor_total:,.2f}
            </p>
        </div>
    """

    bloco_em_aberto = f"""
        <div style="
            background-color: #f35202;
            padding: 13px;
            border-radius: 10px;
            text-align: center;
            flex: 1;
            min-width: 150px;
        ">
            <h4 style="color: #ffffff; margin: 3px; font-weight: 400;">📂 Em Aberto</h4>
            <p style="color: #ffffff; font-size: 1.6rem; margin: 0; font-weight: 700;">
                R$ {valor_em_aberto:,.2f}
            </p>
        </div>
    """

    bloco_pago = f"""
        <div style="
            background-color: #f35202;
            padding: 13px;
            border-radius: 10px;
            text-align: center;
            flex: 1;
            min-width: 150px;
        ">
            <h4 style="color: #ffffff; margin: 3px; font-weight: 400;">✅ Pago</h4>
            <p style="color: #ffffff; font-size: 1.6rem; margin: 0; font-weight: 700;">
                R$ {valor_pago:,.2f}
            </p>
        </div>
    """

    st.markdown(f"""
        <div style="
            display: flex;
            gap: 10px;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-wrap: wrap;
        ">
            {bloco_total}
            {bloco_em_aberto}
            {bloco_pago}
        </div>
    """, unsafe_allow_html=True)
    
    # Layout para próximos elementos
    col1, col2 = st.columns(2)


    # --- 3. GRÁFICO DE ROSCA (DONUT) (JÁ ESTÁ CORRETO) ---
    with col1:
        st.markdown("##### 📊 Composição por Status")
        df_status = df_filtrado.groupby(coluna_status)[coluna_valor].sum().reset_index()
        if not df_status.empty:
            fig_donut = px.pie(
                df_status,
                names=coluna_status,
                values=coluna_valor,
                hole=0.4,
                color=coluna_status,
                color_discrete_map={'PAGO': '#f35202' , 'EM ABERTO': '#313334'}
            )
            fig_donut.update_layout(showlegend=True, height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Sem dados de status para exibir.")

    with col2:
        st.markdown(f"##### 🏆 Top 5 {coluna_entidade.capitalize()}s - Em Aberto")
        df_em_aberto = df_filtrado[df_filtrado[coluna_status] == 'EM ABERTO']
        
        if not df_em_aberto.empty:
            top_5 = df_em_aberto.groupby(coluna_entidade)[coluna_valor].sum().nlargest(5).sort_values(ascending=True).reset_index()

            # Remover prefixo antes do " - " e criar nome limpo
            top_5['nome_limpo'] = top_5[coluna_entidade].apply(lambda x: x.split(" - ", 1)[-1].strip())

            # Abreviar nomes longos
            limite = 25
            top_5['nome_resumido'] = top_5['nome_limpo'].apply(
                lambda x: x if len(x) <= limite else x[:limite] + '...'
            )

            fig_top5 = px.bar(
                top_5,
                y='nome_resumido',
                x=coluna_valor,
                orientation='h',
                text_auto=True,
                hover_data={'nome_limpo': True, coluna_valor: ':.2f'}
            )
            fig_top5.update_traces(
                marker_color='#f35202',
                texttemplate='R$ %{x:,.2f}'
            )
            fig_top5.update_layout(
                height=400,
                yaxis_title=None,
                xaxis_title="Valor (R$)",
                margin=dict(l=10, r=10, t=40, b=10),
                yaxis=dict(tickfont=dict(size=10))
            )
            st.plotly_chart(fig_top5, use_container_width=True)
        else:
            st.info("Não há contas em aberto para exibir no Top 5.")


#     st.markdown("---")
#     st.markdown("#### Detalhamento Completo")
# # ... final da função
#     st.dataframe(df_filtrado.style.format({
#         coluna_valor: "R$ {:,.2f}",
#         "Data Emissao": "{:%d/%m/%Y}",
#         coluna_vencimento: "{:%d/%m/%Y}"
#     }, na_rep="-"), use_container_width=True)

def carregar_dados_financeiros(caminho_arquivo):
    """
    Carrega as abas 'Contas a Receber' e 'Contas a Pagar' de uma planilha Excel.
    """
    try:
        # Carrega as duas abas em DataFrames separados
        df_receber = pd.read_excel(caminho_arquivo, sheet_name="receber")
        df_pagar = pd.read_excel(caminho_arquivo, sheet_name="pagar")

        # --- Padroniza as colunas de 'Contas a Receber' ---
        df_receber['Data Emissao'] = pd.to_datetime(df_receber['Data Emissao'], errors='coerce')
        df_receber['Data Vencimento'] = pd.to_datetime(df_receber['Data Vencimento'], errors='coerce')
        df_receber['Valor'] = pd.to_numeric(df_receber['Valor'], errors='coerce').fillna(0)
        df_receber['Cliente'] = df_receber['Cliente'].str.strip()
        df_receber['Status'] = df_receber['Status'].str.strip()


        # --- Padroniza as colunas de 'Contas a Pagar' ---
        df_pagar['Data Emissao'] = pd.to_datetime(df_pagar['Data Emissao'], errors='coerce')
        df_pagar['Data Vencimento'] = pd.to_datetime(df_pagar['Data Vencimento'], errors='coerce')
        df_pagar['Valor'] = pd.to_numeric(df_pagar['Valor'], errors='coerce').fillna(0)
        df_pagar['Fornecedor'] = df_pagar['Fornecedor'].str.strip()
        df_pagar['Status'] = df_pagar['Status'].str.strip()


        return df_receber, df_pagar

    except FileNotFoundError:
        st.error(f"❌ Erro: Arquivo Financeiro '{caminho_arquivo}' não encontrado.")
        return None, None
    except ValueError as e:
        if "Worksheet" in str(e) and "not found" in str(e):
             st.error(f"❌ Erro: Uma das abas ('Contas a Receber' ou 'Contas a Pagar') não foi encontrada no arquivo. Verifique o nome das abas.")
             return None, None
        else:
            st.error(f"❌ Erro ao ler o arquivo financeiro: {e}")
            return None, None

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

    # STRIP KEY STRING COLUMNS EARLY, INCLUDING VEN_NOME
    if "VEN_NOME" in df_vendas.columns:
        df_vendas["VEN_NOME"] = df_vendas["VEN_NOME"].str.strip()
    else:
        st.error("❌ Coluna 'VEN_NOME' não encontrada no arquivo de vendas.") # Should not happen if selectbox is populated
        return pd.DataFrame() # Return empty if critical column is missing

    if "CLI_RAZ" in df_vendas.columns:
        df_vendas["CLI_RAZ"] = df_vendas["CLI_RAZ"].str.strip()
    if "PED_OBS_INT" in df_vendas.columns:
        df_vendas["PED_OBS_INT"] = df_vendas["PED_OBS_INT"].str.strip()
    # END OF STRIPPING

    df_vendas["DAT_CAD"] = pd.to_datetime(df_vendas["DAT_CAD"], errors="coerce")

    if df_vendas["DAT_CAD"].isna().all():
        st.error("⚠️ Erro ao processar as datas. Verifique o formato no arquivo de vendas.")
        return None

    df_vendas["CLI_RAZ"] = df_vendas["CLI_RAZ"].str.strip() # Already stripped, but safe to keep if order changes
    df_vendas["PED_OBS_INT"] = df_vendas["PED_OBS_INT"].str.strip() # Already stripped
    df_vendas["PED_TOTAL"] = pd.to_numeric(df_vendas["PED_TOTAL"], errors="coerce").fillna(0)

    df_vendas["DAT_CAD_DATE"] = df_vendas["DAT_CAD"].dt.date

    if data_inicial and data_final:
        data_inicial_dt = pd.to_datetime(data_inicial).date()
        data_final_dt = pd.to_datetime(data_final).date()
        df_vendas = df_vendas[
            (df_vendas["DAT_CAD_DATE"] >= data_inicial_dt) &
            (df_vendas["DAT_CAD_DATE"] <= data_final_dt)
        ]
    elif mes_referencia:
        df_vendas = df_vendas[df_vendas["DAT_CAD"].dt.month == mes_referencia]
        ano_atual = datetime.date.today().year
        df_vendas = df_vendas[df_vendas["DAT_CAD"].dt.year == ano_atual]

    if df_vendas.empty: # Check after date filter
        st.warning("⚠️ Nenhuma venda encontrada no período selecionado (após filtro de data).")
        return pd.DataFrame()

    # Filtro de Vendedor
    if vendedor_selecionado and vendedor_selecionado != "Todos":
        # Now VEN_NOME in df_vendas is stripped, and vendedor_selecionado is also stripped.
        # Casing should also match because vendedor_selecionado comes from unique values of this column.
        df_vendas_vendedor_filtrado = df_vendas[df_vendas["VEN_NOME"] == vendedor_selecionado]
        if df_vendas_vendedor_filtrado.empty:
            st.warning(f"⚠️ Nenhuma venda encontrada para o vendedor '{vendedor_selecionado}' (após filtro de vendedor).")
            # You might want to return df_vendas_vendedor_filtrado (which is empty) or df_vendas based on desired behavior
        df_vendas = df_vendas_vendedor_filtrado


    if df_vendas.empty: # Check after seller filter
        # This warning will now be more specific if the seller filter itself results in empty.
        # No need for an explicit warning here if the one inside the seller filter is sufficient.
        return pd.DataFrame()

    nomes_cdp = [
        "DO PEDREIRO DO LITORAL COMERC DE MATERIAIS DE CONSTRUCAO LTD",
        "DO PEDREIRO DO LITORAL COMERCIO DE MATERIAIS DE CONSTRUCAO",
    ]

        # Filtro de tipo de pedido: apenas tipo 'V'
    if "PED_TIPO" in df_vendas.columns:
        df_vendas = df_vendas[df_vendas["PED_TIPO"].str.upper() == "V"]
        if df_vendas.empty:
            st.warning("⚠️ Nenhuma venda encontrada com o tipo de pedido 'V'.")
            return pd.DataFrame()
    else:
        st.warning("⚠️ Coluna 'PED_TIPO' não encontrada na base de vendas.")
        return pd.DataFrame()


    if not com_cdp:
        df_vendas_cdp_filtrado = df_vendas[~df_vendas["CLI_RAZ"].isin(nomes_cdp)]
        if df_vendas_cdp_filtrado.empty and not df_vendas.empty: # only warn if cdp filter made it empty
             st.warning(f"⚠️ Nenhuma venda encontrada após filtro 'Casa do Pedreiro'.")
        df_vendas = df_vendas_cdp_filtrado


    if df_vendas.empty: # Final check
        st.warning("⚠️ Nenhuma venda encontrada após todos os filtros.")
        return pd.DataFrame()

    return df_vendas


# --- FUNÇÃO PROCESSAR_VENDAS (Agora usa filtrar_vendas) ---
def processar_vendas(df_vendas_filtrado):
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        return 0.0, 0.0

    # Filtro base para OPD e faturado
    filtro_opd = (df_vendas_filtrado["PED_OBS_INT"] == "OPD") & (df_vendas_filtrado["PED_STATUS"] == "F")
    total_opd = df_vendas_filtrado[filtro_opd]["PED_TOTAL"].sum()

    # Soma dos valores para AMC
    # total_amc = df_vendas_filtrado[df_vendas_filtrado["PED_OBS_INT"].isin([ "DISTRIBICAO", "DISTRIBUICAO", "DISTRIBUIÇÃO", "LOJA"])]["PED_TOTAL"].sum()

    # Filtro para pedidos de distribuição com status F ou N
    filtro_distribuicao = df_vendas_filtrado["PED_OBS_INT"].isin([ "DISTRIBICAO", "DISTRIBUICAO", "DISTRIBUIÇÃO", "LOJA"]) & (df_vendas_filtrado["PED_STATUS"].isin(["F", "N"]))
    total_amc = df_vendas_filtrado[filtro_distribuicao]["PED_TOTAL"].sum()

    return float(total_opd), float(total_amc)

# --- FUNÇÕES EXISTENTES (calcular_status, comparar_com_metas, gerar_grafico, calcular_dias_uteis) ---
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

    if ano > hoje.year or (ano == hoje.year and mes_referencia < hoje.month):
        return 0

    if mes_referencia == hoje.month:
        data_inicio = hoje
    else:
        data_inicio = datetime.date(ano, mes_referencia, 1)

    if mes_referencia == 12:
        ultimo_dia = datetime.date(ano, 12, 31)
    else:
        ultimo_dia = datetime.date(ano, mes_referencia + 1, 1) - datetime.timedelta(days=1)

    dias = pd.date_range(data_inicio, ultimo_dia).to_list()
    feriados = feriados or []

    dias_uteis_count = 0
    for dia in dias:
        dia_date = dia.date()
        if dia.weekday() < 5 and dia_date not in feriados:
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
    dia_final = min(hoje, datetime.date(ano, mes_referencia + 1, 1) - datetime.timedelta(days=1) if mes_referencia < 12 else datetime.date(ano, 12, 31))

    dias = pd.date_range(primeiro_dia, dia_final).to_list()
    dias_uteis_count = 0
    for dia in dias:
        dia_date = dia.date()
        if dia.weekday() < 5 and dia_date not in feriados:
            if incluir_hoje or dia_date < hoje:
                dias_uteis_count += 1
    return dias_uteis_count


# --- NOVAS FUNÇÕES PARA TABELAS ---

def gerar_tabela_diaria_empresa(df_vendas_filtrado):
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        st.info("Nenhuma venda encontrada para gerar o relatório diário da empresa.")
        return pd.DataFrame()

    df = df_vendas_filtrado.copy()

    # CÓDIGO NOVO E CORRIGIDO
    # Condição para OPD: Observação é OPD E status é F
    cond_opd = (df['PED_OBS_INT'] == 'OPD') & (df['PED_STATUS'] == 'F')

    # Condição para Distribuição: Observação é de distribuição E status é F ou N
    cond_dist = df['PED_OBS_INT'].isin(['DISTRIBICAO', 'DISTRIBUICAO', 'DISTRIBUIÇÃO', 'LOJA']) & df['PED_STATUS'].isin(['F', 'N'])

    # Aplicar as condições usando np.select para criar a coluna 'Tipo Venda'
    df['Tipo Venda'] = np.select(
        [cond_opd, cond_dist],    # Lista de condições a serem checadas
        ['OPD', 'Distribuição'],  # Lista de valores correspondentes
        default='Outros'          # Valor padrão se nenhuma condição for atendida
    )
    df_validos = df[df['Tipo Venda'].isin(['OPD', 'Distribuição'])]

    tabela = pd.pivot_table(
        df_validos,
        values='PED_TOTAL',
        index=df_validos['DAT_CAD'].dt.date,
        columns='Tipo Venda',
        aggfunc=np.sum,
        fill_value=0
    )

    if 'OPD' not in tabela.columns:
        tabela['OPD'] = 0
    if 'Distribuição' not in tabela.columns:
        tabela['Distribuição'] = 0

    tabela['Total Dia'] = tabela['OPD'] + tabela['Distribuição']
    tabela = tabela.sort_index(ascending=True)

    total_geral = tabela.sum().to_frame().T
    total_geral.index = ['**TOTAL GERAL**']
    tabela = pd.concat([tabela, total_geral])

    tabela.index = [idx.strftime('%d/%m/%Y') if isinstance(idx, datetime.date) else idx for idx in tabela.index]
    tabela = tabela.reset_index().rename(columns={'index': 'Data'})

    for col in ['OPD', 'Distribuição', 'Total Dia']:
        tabela[col] = tabela[col].apply(lambda x: f"R$ {x:,.2f}")
    return tabela

def gerar_tabela_geral(df_vendas_filtrado):
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        st.info("Nenhuma venda encontrada para gerar o relatório geral.")
        return pd.DataFrame()

    df = df_vendas_filtrado.copy()

    # CÓDIGO NOVO E CORRIGIDO
    # Condição para OPD: Observação é OPD E status é F
    cond_opd = (df['PED_OBS_INT'] == 'OPD') & (df['PED_STATUS'] == 'F')

    # Condição para Distribuição: Observação é de distribuição E status é F ou N
    cond_dist = df['PED_OBS_INT'].isin(['DISTRIBICAO', 'DISTRIBUICAO', 'DISTRIBUIÇÃO', 'LOJA']) & df['PED_STATUS'].isin(['F', 'N'])

    # Aplicar as condições usando np.select para criar a coluna 'Tipo Venda'
    df['Tipo Venda'] = np.select(
        [cond_opd, cond_dist],    # Lista de condições a serem checadas
        ['OPD', 'Distribuição'],  # Lista de valores correspondentes
        default='Outros'          # Valor padrão se nenhuma condição for atendida
    )
    df_validos = df[df['Tipo Venda'].isin(['OPD', 'Distribuição'])]

    tabela = pd.pivot_table(
        df_validos,
        values='PED_TOTAL',
        index='VEN_NOME',
        columns='Tipo Venda',
        aggfunc=np.sum,
        fill_value=0
    )

    if 'OPD' not in tabela.columns:
        tabela['OPD'] = 0
    if 'Distribuição' not in tabela.columns:
        tabela['Distribuição'] = 0

    tabela['Total Vendedor'] = tabela['OPD'] + tabela['Distribuição']
    tabela = tabela.sort_values(by='Total Vendedor', ascending=False)

    total_geral = tabela.sum().to_frame().T
    total_geral.index = ['**TOTAL GERAL**']
    tabela = pd.concat([tabela, total_geral])

    for col in ['OPD', 'Distribuição', 'Total Vendedor']:
        tabela[col] = tabela[col].apply(lambda x: f"R$ {x:,.2f}")
    return tabela.reset_index().rename(columns={'VEN_NOME': 'Vendedor'})


def gerar_tabela_vendedor(df_vendas_filtrado):
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        st.info("Nenhuma venda encontrada para este vendedor no período.")
        return pd.DataFrame(), {}

    df = df_vendas_filtrado.copy()

    # CÓDIGO NOVO E CORRIGIDO
    # Condição para OPD: Observação é OPD E status é F
    cond_opd = (df['PED_OBS_INT'] == 'OPD') & (df['PED_STATUS'] == 'F')

    # Condição para Distribuição: Observação é de distribuição E status é F ou N
    cond_dist = df['PED_OBS_INT'].isin(['DISTRIBICAO', 'DISTRIBUICAO', 'DISTRIBUIÇÃO', 'LOJA']) & df['PED_STATUS'].isin(['F', 'N'])

    # Aplicar as condições usando np.select para criar a coluna 'Tipo Venda'
    df['Tipo Venda'] = np.select(
        [cond_opd, cond_dist],    # Lista de condições a serem checadas
        ['OPD', 'Distribuição'],  # Lista de valores correspondentes
        default='Outros'          # Valor padrão se nenhuma condição for atendida
    )
    df_validos = df[df['Tipo Venda'].isin(['OPD', 'Distribuição'])]

    total_opd = df_validos[df_validos['Tipo Venda'] == 'OPD']['PED_TOTAL'].sum()
    total_dist = df_validos[df_validos['Tipo Venda'] == 'Distribuição']['PED_TOTAL'].sum()
    totais = {
        'OPD': total_opd,
        'Distribuição': total_dist,
        'Total': total_opd + total_dist
    }

    tabela = df_validos[[
        'DAT_CAD',
        'VEN_NOME',
        'CLI_RAZ',
        'PED_TOTAL',
        'Tipo Venda'
    ]].copy()

    tabela.rename(columns={
        'VEN_NOME': 'Vendedor',
        'CLI_RAZ': 'Cliente',
        'PED_TOTAL': 'Valor',
    }, inplace=True)

    tabela = tabela.sort_values(by='DAT_CAD', ascending=True)
    tabela['Data'] = tabela['DAT_CAD'].dt.strftime('%d/%m/%Y')
    tabela['Valor'] = tabela['Valor'].apply(lambda x: f"R$ {x:,.2f}")

    tabela_final = tabela[[
        'Data',
        'Vendedor',
        'Cliente',
        'Valor',
        'Tipo Venda'
    ]]
    return tabela_final, totais

def gerar_dados_ranking(df_vendas_filtrado):
    """
    Prepara os dados para o ranking de vendedores, mantendo os valores numéricos.
    """
    if df_vendas_filtrado is None or df_vendas_filtrado.empty:
        return pd.DataFrame()

    df = df_vendas_filtrado.copy()
    # CÓDIGO NOVO E CORRIGIDO
    # Condição para OPD: Observação é OPD E status é F
    cond_opd = (df['PED_OBS_INT'] == 'OPD') & (df['PED_STATUS'] == 'F')

    # Condição para Distribuição: Observação é de distribuição E status é F ou N
    cond_dist = df['PED_OBS_INT'].isin(['DISTRIBICAO', 'DISTRIBUICAO', 'DISTRIBUIÇÃO', 'LOJA']) & df['PED_STATUS'].isin(['F', 'N'])

    # Aplicar as condições usando np.select para criar a coluna 'Tipo Venda'
    df['Tipo Venda'] = np.select(
        [cond_opd, cond_dist],    # Lista de condições a serem checadas
        ['OPD', 'Distribuição'],  # Lista de valores correspondentes
        default='Outros'          # Valor padrão se nenhuma condição for atendida
    )
    df_validos = df[df['Tipo Venda'].isin(['OPD', 'Distribuição'])]

    tabela = pd.pivot_table(
        df_validos,
        values='PED_TOTAL',
        index='VEN_NOME',
        columns='Tipo Venda',
        aggfunc='sum',
        fill_value=0
    )

    if 'OPD' not in tabela.columns: tabela['OPD'] = 0
    if 'Distribuição' not in tabela.columns: tabela['Distribuição'] = 0

    return tabela.reset_index().rename(columns={'VEN_NOME': 'Vendedor'})


# --- INTERFACE STREAMLIT ---

# Onde você tem o st.sidebar.radio

st.sidebar.title("📊 Navegação")
pagina_selecionada = st.sidebar.radio(
    "Escolha a visualização:",
    ["Painel Principal", "Relatórios Financeiros"] # <-- ADICIONE AQUI
)

st.title(f"📈 {pagina_selecionada}")

caminho_metas = "resources/META.xlsx"
caminho_vendas_padrao = "resources/VENDAS.xlsx"
uploaded_file = caminho_vendas_padrao
feriados = carregar_feriados()

st.sidebar.header("Filtros")
filtro_tipo = st.sidebar.radio("🔍 Tipo de filtro:", ["Mês", "Período Personalizado"])

mes_selecionado = None
data_inicial, data_final = None, None

if filtro_tipo == "Mês":
    mes_selecionado = st.sidebar.selectbox(
        "📅 Mês de referência", range(1, 13),
        format_func=lambda x: ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][x - 1],
        index=datetime.date.today().month - 1
    )
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
            st.stop()
        mes_selecionado = data_final.month
    else:
        st.sidebar.error("⚠️ Selecione uma data inicial e uma data final!")
        st.stop()

try:
    df_vendas_bruto = pd.read_excel(uploaded_file)
    vendedores_unicos_stripped = sorted(list(df_vendas_bruto["VEN_NOME"].dropna().str.strip().unique()))
    vendedores = ["Todos"] + vendedores_unicos_stripped
    vendedor_selecionado = st.sidebar.selectbox("👤 Vendedor", vendedores)
except FileNotFoundError:
    st.error(f"❌ Erro: Arquivo '{uploaded_file}' não encontrado. Verifique o caminho.")
    st.stop()

com_cdp = st.sidebar.checkbox("Incluir vendas da Casa do Pedreiro", value=True)

# --- Seleção da Aba de Metas ---
# As listas como rose_loja devem conter os nomes EXATOS e LIMPOS (e em MAIÚSCULAS para a comparação abaixo)
rose_loja = ["ROSESILVESTRE"]
paola_loja = ["PAOLA"]
jemine_loja = ["JEMINE OLIVEIRA"]
danilima_d = ["DANILIMA"]
renato_d = ["JOSE RENATO MAULER"] # Assumindo que este também é o formato esperado em MAIÚSCULAS

# 'vendedor_selecionado' já deve vir limpo do selectbox (sem espaços extras)
# MODIFICAÇÃO APLICADA AQUI:
vendedor_selecionado_upper = vendedor_selecionado.upper() # Converte para maiúsculas para comparação


####################################################################################################
if vendedor_selecionado == "Todos": # "Todos" é um valor especial, não precisa de .upper()
    aba_meta_calculada = "GERAL"

elif vendedor_selecionado_upper in paola_loja:
    aba_meta_calculada = "PAOLA"

elif vendedor_selecionado_upper in jemine_loja:
    aba_meta_calculada = "JEMINE"

elif vendedor_selecionado_upper in danilima_d:
    aba_meta_calculada = "DANILIMA"

elif vendedor_selecionado_upper in renato_d:
    aba_meta_calculada = "RENATO"

elif vendedor_selecionado_upper in rose_loja: # Compara "NOMEEMMAIUSCULAS" com ["ROSESILVESTRE"]
    aba_meta_calculada = "ROSE"

else:
    aba_meta_calculada = "GERAL"

# --- Fim da Seleção da Aba de Metas ---
######################################################################################################


if st.sidebar.button("🔄 Processar Dados"):
    with st.spinner("🔄 Processando..."):
        # st.sidebar.info(f"Vendedor selecionado (original): {vendedor_selecionado}")
        # st.sidebar.info(f"Tentando carregar metas da aba: '{aba_meta_calculada}'")

        df_filtrado = filtrar_vendas(
            uploaded_file,
            mes_selecionado if filtro_tipo == "Mês" else None,
            vendedor_selecionado,
            data_inicial,
            data_final,
            com_cdp
        )

        planilha_metas = None
        try:
            planilha_metas = carregar_planilha_metas(caminho_metas, aba=aba_meta_calculada)
            if planilha_metas.empty:
                st.sidebar.warning(f"⚠️ Planilha de metas para aba '{aba_meta_calculada}' está vazia.")
                planilha_metas = None
        except FileNotFoundError:
            st.error(f"❌ Erro: Arquivo de Metas '{caminho_metas}' não encontrado.")
        except ValueError as ve:
            if "Worksheet" in str(ve) and "not found" in str(ve):
                st.error(f"❌ Erro: A aba '{aba_meta_calculada}' não foi encontrada no arquivo de metas. Verifique o nome da aba.")
            else:
                st.error(f"❌ Erro ao carregar planilha de metas: {ve}")
        except Exception as e:
            st.error(f"❌ Erro desconhecido ao carregar a aba '{aba_meta_calculada}' da planilha de metas: {e}")

        if df_filtrado is not None and not df_filtrado.empty:
            total_opd, total_amc = processar_vendas(df_filtrado)
        else:
            total_opd, total_amc = 0.0, 0.0

        comparacao = {}
        if planilha_metas is not None and mes_selecionado:
            comparacao = comparar_com_metas(planilha_metas, mes_selecionado, total_opd, total_amc)
            if not comparacao :
                st.sidebar.warning(f"⚠️ Não foi possível gerar a comparação de metas para a aba '{aba_meta_calculada}' e mês {mes_selecionado}. Verifique se as categorias de meta existem nessa aba.")
        elif planilha_metas is None:
            st.sidebar.error(f"Metas não puderam ser carregadas da aba '{aba_meta_calculada}'. A comparação não será feita.")

        st.session_state['df_filtrado'] = df_filtrado
        st.session_state['total_opd'] = total_opd
        st.session_state['total_amc'] = total_amc
        st.session_state['comparacao'] = comparacao
        st.session_state['mes_selecionado'] = mes_selecionado
        st.session_state['feriados'] = feriados
        st.session_state['vendedor_selecionado'] = vendedor_selecionado
        st.session_state['aba_meta_usada'] = aba_meta_calculada


if 'df_filtrado' not in st.session_state:
    st.info("📂 Selecione os filtros na barra lateral e clique em 'Processar Dados'.")
else:
    df_filtrado = st.session_state['df_filtrado']
    total_opd = st.session_state['total_opd']
    total_amc = st.session_state['total_amc']
    comparacao = st.session_state['comparacao']
    mes = st.session_state['mes_selecionado']
    feriados_sess = st.session_state['feriados'] # Renomeado para evitar conflito com a variável global
    vendedor_selecionado_sess = st.session_state['vendedor_selecionado'] # Renomeado

    if pagina_selecionada == "Painel Principal":
        tab1, tab2 = st.tabs(["📊 Visão Geral", "📋 Relatórios Detalhados"])
        with tab1:
            if df_filtrado is None or df_filtrado.empty:
                st.warning("Nenhum dado para exibir no Painel Principal com os filtros atuais.")
            elif not comparacao:
                st.warning("Metas não carregadas ou não encontradas para os filtros. O painel será exibido sem comparações.")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📈 Vendas OPD", f"R$ {total_opd:,.2f}")
                with col2:
                    st.metric("📊 Vendas Distribuição", f"R$ {total_amc:,.2f}")
            else:
                dias_uteis_passados = calcular_dias_uteis_passados(mes, incluir_hoje=False, feriados=feriados_sess)
                dias_uteis_restantes = calcular_dias_uteis_restantes(mes, incluir_hoje=True, feriados=feriados_sess)
                # Evita divisão por zero se não houver dias passados/restantes no mês (ex: primeiro/último dia)
                dias_uteis_passados_calc = max(1, dias_uteis_passados)
                dias_uteis_restantes_calc = max(1, dias_uteis_restantes)


                def format_valor(valor):
                    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                def calcular_tendencia(realizado, dias_passados, dias_futuros):
                    if dias_passados == 0: # Se não houve dias úteis passados no período filtrado
                        media_diaria = 0
                        tendencia_total = realizado # A tendência é apenas o que já foi realizado
                    else:
                        media_diaria = realizado / dias_passados
                        tendencia_total = realizado + (media_diaria * dias_futuros)
                    return tendencia_total, media_diaria

                if vendedor_selecionado_sess == "Todos":
                    soma_total = total_opd + total_amc
                    realizado_geral = soma_total
                    meta_geral = comparacao.get("OPD", {}).get("Meta Mensal", 0) + comparacao.get("AMC", {}).get("Meta Mensal", 0)
                    meta_desafio = comparacao.get("OPD", {}).get("Meta Desafio", 0) + comparacao.get("AMC", {}).get("Meta Desafio", 0)
                    super_meta = comparacao.get("AMC", {}).get("Super Meta", 0) + comparacao.get("OPD", {}).get("Meta Desafio", 0)

                    def gerar_bloco_meta(titulo, meta_valor):
                        tendencia, media_diaria = calcular_tendencia(realizado_geral, dias_uteis_passados_calc, dias_uteis_restantes_calc)
                        necessario_por_dia = max(0, (meta_valor - realizado_geral) / dias_uteis_restantes_calc) if dias_uteis_restantes_calc > 0 else (meta_valor - realizado_geral)

                        html = (
                            f"<div style='background-color:#161616; padding:10px; border-radius:10px; width:33%; text-align:center; margin-bottom:10px;'>"
                            f"<h4 style='color:#ffffff;'>{titulo}: {format_valor(meta_valor)}</h4>"
                            f"<p style='color:#cccccc; margin:4px;'>📈 Tendência: {format_valor(tendencia)}</p>"
                            f"<p style='color:#cccccc; margin:4px;'>📊 Média Diária Realizada: {format_valor(media_diaria)}</p>"
                            f"<p style='color:#cccccc; margin:4px;'>🎯 Necessário/dia (restante): {format_valor(necessario_por_dia)}</p>"
                            f"</div>"
                        )
                        return html

                    bloco_mensal = gerar_bloco_meta("Meta Mensal", meta_geral)
                    bloco_desafio = gerar_bloco_meta("Meta Desafio", meta_desafio)
                    bloco_super = gerar_bloco_meta("Super Meta", super_meta)

                    st.markdown(f"<div style='background-color:#161616; padding:20px; border-radius:10px; text-align:center; margin-top:10px; margin-bottom:10px;'><h3 style='color:#ffffff;'>💰 Total Geral da Empresa: {format_valor(soma_total)}</h3></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='display: flex; justify-content: space-between; gap: 10px; margin-top:0px;'>{bloco_mensal}{bloco_desafio}{bloco_super}</div>", unsafe_allow_html=True)

                col1_chart, col2_chart = st.columns(2)
                with col1_chart:
                    st.markdown(f"<div style='background-color:#f35202; padding:10px; border-radius:10px; text-align:center;'><h4 style='color:#ffff;'>📈 Vendas OPD: R$ {total_opd:,.2f}</h4></div>", unsafe_allow_html=True)
                    if "OPD" in comparacao and comparacao["OPD"]:
                        st.plotly_chart(gerar_grafico("OPD", comparacao["OPD"], "Relação de OPD"), use_container_width=True)
                    else:
                        st.info("Dados de OPD não disponíveis para o gráfico.")
                with col2_chart:
                    st.markdown(f"<div style='background-color:#f35202; padding:10px; border-radius:10px; text-align:center;'><h4 style='color:#ffff;'>📊 Vendas Distribuição: R$ {total_amc:,.2f}</h4></div>", unsafe_allow_html=True)
                    if "AMC" in comparacao and comparacao["AMC"]:
                        st.plotly_chart(gerar_grafico("AMC", comparacao["AMC"], "Relação de Distribuição"), use_container_width=True)
                    else:
                        st.info("Dados de Distribuição (AMC) não disponíveis para o gráfico.")


                st.markdown("<h2 style='text-align: center; margin-top: 30px;'>📢 Status Detalhado das Metas</h2>", unsafe_allow_html=True)
                col1_m, col2_m = st.columns(2)

                def exibir_metricas(coluna, titulo, metas_cat, realizado_cat):
                    with coluna:
                        st.markdown(f"<div style='text-align: center; font-size: 25px; font-weight: bold; margin-bottom: 15px;'>{titulo}</div>", unsafe_allow_html=True)
                        tendencia, media_diaria = calcular_tendencia(realizado_cat, dias_uteis_passados_calc, dias_uteis_restantes_calc)

                        for nome_meta, valor_meta in metas_cat.items():
                            if nome_meta == "Realizado" or valor_meta <= 0: continue

                            necessario = max(0, (valor_meta - realizado_cat) / dias_uteis_restantes_calc) if dias_uteis_restantes_calc > 0 else (valor_meta - realizado_cat)
                            delta_color = "normal" # Default to normal (red for negative delta in st.metric)
                            diferenca_tendencia_meta = tendencia - valor_meta
                            percentual_tendencia = (diferenca_tendencia_meta / valor_meta) * 100 if valor_meta > 0 else 0


                            st.metric(
                                label=f"🎯 {nome_meta}",
                                value=format_valor(valor_meta),
                                delta=f"Necessário vender por dia: {format_valor(necessario)}",
                                delta_color="off" # Let the custom HTML handle colors based on trend
                            )

                            if tendencia >= valor_meta:
                                cor_borda = "#28a745" # Verde
                                sinal = "+"
                                texto_status = f"📈 Tendência positiva para <u>{nome_meta}</u>"
                                texto_rodape = f"Projeção de ultrapassar a meta em {sinal}{format_valor(abs(diferenca_tendencia_meta))}."
                            else:
                                cor_borda = "#dc3545" # Vermelho
                                sinal = "-"
                                texto_status = f"📉 Risco de não atingir <u>{nome_meta}</u>"
                                texto_rodape = f"Projeção de ficar abaixo da meta em {sinal}{format_valor(abs(diferenca_tendencia_meta))}."

                            texto_html = f"""
                            <div style="background-color:#161616; padding:16px; border-radius:12px; margin-bottom:15px;
                                        box-shadow:0 2px 6px rgba(0,0,0,0.1); border-left:6px solid {cor_borda};">
                                <div style="font-size:16px; font-weight:bold;">{texto_status}</div>
                                <div style="font-size:22px; font-weight:bold; color:{cor_borda}; margin-top:6px;">
                                    {sinal}{format_valor(abs(diferenca_tendencia_meta))} ({sinal}{abs(percentual_tendencia):.1f}%)
                                </div>
                                <div style="font-size:14px; color:#cccccc;">{texto_rodape}</div>
                                <div style="font-size:14px; color:#cccccc; margin-top:5px;">
                                    <i>Tendência Total: {format_valor(tendencia)} | Média Diária Realizada: {format_valor(media_diaria)}</i>
                                </div>
                            </div>
                            """
                            st.markdown(texto_html, unsafe_allow_html=True)
                            st.markdown("---")

                if "OPD" in comparacao and comparacao["OPD"]:
                    metas_opd_validas = {k: v for k, v in comparacao["OPD"].items() if v > 0 and k != "Realizado"}
                    exibir_metricas(col1_m, "📦 OPD", metas_opd_validas, total_opd)
                else:
                    with col1_m:
                        st.info("Dados de metas OPD não disponíveis.")

                if "AMC" in comparacao and comparacao["AMC"]:
                    metas_amc_validas = {k: v for k, v in comparacao["AMC"].items() if v > 0 and k != "Realizado"}
                    exibir_metricas(col2_m, "🚚 Distribuição", metas_amc_validas, total_amc)
                else:
                    with col2_m:
                        st.info("Dados de metas Distribuição (AMC) não disponíveis.")

        with tab2:
            if df_filtrado is None or df_filtrado.empty:
                st.warning("Nenhum dado para exibir nos Relatórios com os filtros atuais.")
            else:
                if vendedor_selecionado_sess == "Todos":
                    st.subheader("📋 Visão Geral da Empresa")
                    tipo_visao_geral = st.radio(
                        "Escolha como visualizar os dados gerais:",
                        ["Resumo por Vendedor", "Resumo Dia a Dia (Empresa)"],
                        horizontal=True
                    )
                    if tipo_visao_geral == "Resumo por Vendedor":
                        st.markdown("##### Total de Vendas por Vendedor")
                        tabela_geral_df = gerar_tabela_geral(df_filtrado)
                        st.dataframe(tabela_geral_df, use_container_width=True)
                    elif tipo_visao_geral == "Resumo Dia a Dia (Empresa)":
                        st.markdown("##### Vendas Resumidas da Empresa (Dia a Dia)")
                        tabela_resumo_dia_df = gerar_tabela_diaria_empresa(df_filtrado)
                        st.dataframe(tabela_resumo_dia_df, use_container_width=True)

                    # --- Ranking apenas se "Todos" estiver selecionado, dentro do tab2 ---
                    st.markdown("---")
                    st.subheader("🏆 Ranking de Vendedores no Período")

                    df_ranking = gerar_dados_ranking(df_filtrado)

                    if not df_ranking.empty:
                        col1, col2 = st.columns(2)
                        for tipo_rank, col in zip(["OPD", "Distribuição"], [col1, col2]):
                            if tipo_rank in df_ranking.columns and df_ranking[tipo_rank].sum() > 0:
                                with col:
                                    st.markdown(f"##### {tipo_rank}")
                                    df_sorted = df_ranking.sort_values(by=tipo_rank, ascending=False)
                                    df_top3 = df_sorted.head(3).copy()

                                    # Cores ouro, prata, bronze
                                    cores = ['#e02500', '#e93900', '#f35202']
                                    df_top3['Cor'] = cores[:len(df_top3)]

                                    fig = px.bar(
                                        df_top3.sort_values(by=tipo_rank, ascending=True),
                                        x=tipo_rank, y="Vendedor",
                                        orientation='h',
                                        text_auto=True,
                                        color='Cor',
                                        color_discrete_map={c: c for c in cores}
                                    )
                                    fig.update_traces(texttemplate='R$ %{x:,.2f}')
                                    fig.update_layout(height=300, showlegend=False)
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                with col:
                                    st.info(f"Nenhuma venda '{tipo_rank}' encontrada.")
                    else:
                        st.info("Ranking não pôde ser gerado. Verifique os dados.")

                else:
                    st.subheader(f"📋 Detalhe de Vendas - {vendedor_selecionado_sess}")
                    tabela_detalhada, totais_vendedor = gerar_tabela_vendedor(df_filtrado)
                    if not tabela_detalhada.empty:
                        st.dataframe(tabela_detalhada, use_container_width=True)
                        st.markdown("---")
                        st.subheader("Resumo do Vendedor no Período")
                        col1_vend, col2_vend, col3_vend = st.columns(3)
                        col1_vend.metric("🔹 Total OPD", f"R$ {totais_vendedor.get('OPD', 0):,.2f}")
                        col2_vend.metric("🔸 Total Distribuição", f"R$ {totais_vendedor.get('Distribuição', 0):,.2f}")
                        col3_vend.metric("💰 Total Geral Vendedor", f"R$ {totais_vendedor.get('Total', 0):,.2f}")


    # --------------------------------------------------------------------------------
    # NOVA PÁGINA: RELATÓRIOS FINANCEIROS
    # --------------------------------------------------------------------------------
    elif pagina_selecionada == "Relatórios Financeiros":
        
        # st.markdown("## 💰 Painel Financeiro")
        # st.markdown("---")

        caminho_financeiro = "resources/FINANCEIRO.xlsx"
        df_receber, df_pagar = carregar_dados_financeiros(caminho_financeiro)

        if df_receber is not None and df_pagar is not None:
            
            # --- FILTROS ESPECÍFICOS PARA O FINANCEIRO ---
            # Usaremos os filtros de data já existentes na sidebar, mas adicionaremos filtros de cliente/fornecedor aqui.
            
            st.sidebar.header("Filtros Financeiros")
            
            # Filtro de Status
            lista_status = pd.concat([df_receber['Status'], df_pagar['Status']]).dropna().unique().tolist()
            status_selecionados = st.sidebar.multiselect("Filtrar por Status", options=lista_status, default=lista_status)

            # Filtro de Cliente/Fornecedor
            lista_entidades = pd.concat([df_receber['Cliente'], df_pagar['Fornecedor']]).dropna().unique().tolist()
            entidades_selecionadas = st.sidebar.multiselect("Filtrar por Cliente/Fornecedor", options=lista_entidades, default=lista_entidades)

            # Aplicando filtros
            df_receber_filtrado = df_receber[
                (df_receber['Data Vencimento'].dt.date >= data_inicial) &
                (df_receber['Data Vencimento'].dt.date <= data_final) &
                (df_receber['Status'].isin(status_selecionados)) &
                (df_receber['Cliente'].isin(entidades_selecionadas))
            ]
            
            df_pagar_filtrado = df_pagar[
                (df_pagar['Data Vencimento'].dt.date >= data_inicial) &
                (df_pagar['Data Vencimento'].dt.date <= data_final) &
                (df_pagar['Status'].isin(status_selecionados)) &
                (df_pagar['Fornecedor'].isin(entidades_selecionadas))
            ]

            # --- ABAS PARA VISUALIZAÇÃO ---
            tab1, tab2 = st.tabs(["📊 Contas a Receber", "💸 Contas a Pagar"])

            with tab1:
                # NOVO CÓDIGO DENTRO DE "with tab1:"
                criar_painel_financeiro_avancado(
                    "📊 Visão Geral de Contas a Receber",
                    df_receber_filtrado,
                    coluna_valor='Valor',
                    coluna_status='Status',
                    coluna_entidade='Cliente',
                    coluna_vencimento='Data Vencimento'
)

            with tab2:
                # NOVO CÓDIGO DENTRO DE "with tab2:"
                criar_painel_financeiro_avancado(
                    "💸 Visão Geral de Contas a Pagar",
                    df_pagar_filtrado,
                    coluna_valor='Valor',
                    coluna_status='Status',
                    coluna_entidade='Fornecedor',
                    coluna_vencimento='Data Vencimento'
                )
                
        else:
            st.warning("⚠️ Não foi possível carregar os dados financeiros. Verifique o arquivo e as abas.")
