import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Construtora Pro - Gestão", layout="wide", initial_sidebar_state="collapsed")

# Estilo para botões e métricas
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE ARQUIVOS ---
BASE_PATH = "DADOS_CONSTRUTORA"
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)

def carregar_dados(nome_arq, colunas):
    caminho = os.path.join(BASE_PATH, nome_arq)
    if not os.path.exists(caminho):
        pd.DataFrame(columns=colunas).to_csv(caminho, index=False)
    return pd.read_csv(caminho)

def salvar_dados(df, nome_arq):
    df.to_csv(os.path.join(BASE_PATH, nome_arq), index=False)

# --- INTERFACE PRINCIPAL ---
st.title("🏗️ Gestão de Obras & Vendas")
st.info("Painel de Controlo Integrado")

abas = st.tabs(["📊 Dashboard", "📝 Nova Obra", "🧱 Obras e Unidades", "🧾 Pagamentos", "📋 Cronograma", "💰 Venda Final"])

# --- 1. DASHBOARD ---
with abas[0]:
    df_f = carregar_dados('financeiro.csv', ['Obra', 'Tipo', 'Item', 'Valor'])
    if not df_f.empty:
        obra_sel = st.selectbox("Filtrar Obra:", df_f['Obra'].unique())
        dados_obra = df_f[df_f['Obra'] == obra_sel]
        orcado = dados_obra[dados_obra['Tipo'] == 'ORÇADO']['Valor'].sum()
        gasto = dados_obra[dados_obra['Tipo'] == 'REALIZADO']['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento", f"R$ {orcado:,.2f}")
        c2.metric("Gasto Real", f"R$ {gasto:,.2f}", delta=f"R$ {orcado-gasto} rest.")
        c3.metric("Status", "Em Andamento" if gasto < orcado else "Atenção!", delta_color="inverse")
        st.progress(min(gasto/orcado, 1.0) if orcado > 0 else 0)
    else:
        st.write("Sem dados para exibir.")

# --- 2. NOVA OBRA ---
with abas[1]:
    with st.form("nova_obra"):
        nome = st.text_input("Nome do Empreendimento")
        orc_estimado = st.number_input("Orçamento Global Previsto", min_value=0.0)
        if st.form_submit_button("Criar Obra"):
            df_f = carregar_dados('financeiro.csv', ['Obra', 'Tipo', 'Item', 'Valor'])
            novo = pd.DataFrame([[nome, 'ORÇADO', 'Estimativa Inicial', orc_estimado]], columns=df_f.columns)
            salvar_dados(pd.concat([df_f, novo]), 'financeiro.csv')
            # Gerar tarefas padrão
            df_t = carregar_dados('tarefas.csv', ['Obra', 'Cat', 'Tarefa', 'Status', 'Vencimento'])
            tarefas = [("Doc", "Alvará"), ("Obra", "Fundação"), ("Doc", "Habite-se")]
            novas_t = pd.DataFrame([(nome, c, t, "🔴", "") for c, t in tarefas], columns=df_t.columns)
            salvar_dados(pd.concat([df_t, novas_t]), 'tarefas.csv')
            st.success("Obra e Cronograma iniciados!")

# --- 3. UNIDADES E FOTOS ---
with abas[2]:
    df_u = carregar_dados('unidades.csv', ['Obra', 'Unidade'])
    if not df_f.empty:
        obra_u = st.selectbox("Obra:", df_f['Obra'].unique(), key="u_obra")
        u_nome = st.text_input("Nova Unidade (ex: Apt 101)")
        if st.button("Cadastrar Unidade"):
            salvar_dados(pd.concat([df_u, pd.DataFrame([[obra_u, u_nome]], columns=df_u.columns)]), 'unidades.csv')
            os.makedirs(os.path.join(BASE_PATH, obra_u, u_nome, "Fotos"), exist_ok=True)
            st.success("Pasta criada!")
        
        cam = st.camera_input("Foto da Unidade")
        if cam:
            p_foto = os.path.join(BASE_PATH, obra_u, u_nome, "Fotos", f"{datetime.now().strftime('%H%M%S')}.jpg")
            os.makedirs(os.path.dirname(p_foto), exist_ok=True)
            Image.open(cam).save(p_foto)
            st.success("Foto salva!")

# --- 4. PAGAMENTOS E NOTAS ---
with abas[3]:
    st.subheader("Anexar Nota Fiscal")
    if not df_f.empty:
        o_pag = st.selectbox("Obra:", df_f['Obra'].unique(), key="p_obra")
        v_pag = st.number_input("Valor da Nota", min_value=0.0)
        d_pag = st.text_input("Descrição do Gasto")
        foto_nf = st.camera_input("Tirar foto da NF")
        if st.button("Salvar Pagamento"):
            df_f = carregar_dados('financeiro.csv', ['Obra', 'Tipo', 'Item', 'Valor'])
            novo_p = pd.DataFrame([[o_pag, 'REALIZADO', d_pag, v_pag]], columns=df_f.columns)
            salvar_dados(pd.concat([df_f, novo_p]), 'financeiro.csv')
            st.success("Gasto e Nota registrados!")

# --- 5. CRONOGRAMA ---
with abas[4]:
    df_t = carregar_dados('tarefas.csv', ['Obra', 'Cat', 'Tarefa', 'Status', 'Vencimento'])
    st.dataframe(df_t)

# --- 6. VENDA FINAL ---
with abas[5]:
    st.subheader("Simulador de Lucro Líquido")
    # Lógica de Markup Divisor (Simplificada para o exemplo)
    custo = st.number_input("Custo de Construção", value=100000.0)
    margem = st.slider("Lucro %", 0, 100, 30)
    imposto = st.number_input("Imposto %", value=6.0)
    comissao = st.number_input("Comissão %", value=5.0)
    
    markup = 1 - ((margem + imposto + comissao)/100)
    preco = custo / markup if markup > 0 else 0
    st.metric("Sugerido para Venda", f"R$ {preco:,.2f}")