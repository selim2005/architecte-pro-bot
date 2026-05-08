import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION RESPONSIVE ---
st.set_page_config(page_title="KASAA TRADE PRO", layout="wide", initial_sidebar_state="expanded")

# --- DESIGN PREMIUM PC/MOBILE ---
st.markdown("""
    <style>
    /* Global Look */
    .stApp { background-color: #0E1117; color: white; }
    
    /* Cartes de stats adaptatives */
    .metric-card {
        background: #1C2128;
        padding: 15px;
        border-radius: 10px;
        border-top: 4px solid #00ffbb;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label { color: #8B949E; font-size: 12px; font-weight: bold; }
    .metric-value { font-size: 20px; font-weight: bold; }
    
    /* Sticky Header pour PC */
    @media (min-width: 768px) {
        .fixed-top { position: sticky; top: 0; z-index: 999; background: #0E1117; padding-bottom: 20px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- BARRE LATÉRALE (Paramètres) ---
with st.sidebar:
    st.title("🛡️ KASAA CONFIG")
    api_token = st.text_input("TON JETON API", type="password")
    market = st.selectbox("MARCHÉ", ["1HZ10V", "1HZ50V", "C_300", "B_300"])
    st.button("🚀 DÉMARRER LE BOT")

# --- ZONE FIXE (GRAPHE ET STATS) ---
header = st.container()
with header:
    st.markdown('<div class="fixed-top">', unsafe_allow_html=True)
    
    # Ligne 1 : Les 4 Colonnes de Stats (Responsive)
    s1, s2, s3, s4 = st.columns([1, 1, 1, 1])
    
    # Simulation de données pour l'exemple
    stats = st.session_state.get('stats', {'gains': 0, 'pertes': 0, 'somme_gains': 0.0, 'somme_pertes': 0.0})
    
    s1.markdown(f'<div class="metric-card"><p class="metric-label">✅ GAINS</p><p class="metric-value">{stats["gains"]}</p></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="metric-card"><p class="metric-label">❌ PERTES</p><p class="metric-value">{stats["pertes"]}</p></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="metric-card"><p class="metric-label">💰 ENCAISSÉ</p><p class="metric-value" style="color:#00ffbb">+{stats["somme_gains"]}$</p></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="metric-card"><p class="metric-label">📉 PERDU</p><p class="metric-value" style="color:#ff3333">-{stats["somme_pertes"]}$</p></div>', unsafe_allow_html=True)

    # Ligne 2 : Le Graphique
    # (Ici, on met une hauteur fixe de 400 pour que ça tienne sur mobile)
    fig = go.Figure(data=[go.Candlestick(x=[1,2,3], open=[10,11,12], high=[12,13,14], low=[9,10,11], close=[11,12,13])])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- ZONE DÉFILANTE (HISTORIQUE) ---
st.markdown("### 📜 HISTORIQUE LIVE")
if 'logs' in st.session_state:
    st.table(pd.DataFrame(st.session_state.logs))
else:
    st.info("En attente de trades...")