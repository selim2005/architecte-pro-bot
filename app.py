import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import asyncio
from bot_test import executer_ordre_automatique

# Configuration visuelle Premium
st.set_page_config(page_title="KASAA TRADE - SYSTÈME PRO", layout="wide")

# CSS pour bloquer le graphique en haut et style sombre
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] { background-color: #1c212d; border: 1px solid #00ff88; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'stats' not in st.session_state:
    st.session_state.stats = {'profit': 0.0, 'victoires': 0, 'pertes': 0, 'martingale': 0, 'logs': []}

# --- TITRE ET STATISTIQUES ---
st.title("💎 KASAA TRADE - L'Architecte Pro")

col_stats = st.columns(3)
col_stats[0].metric("PROFIT TOTAL", f"{st.session_state.stats['profit']:.2f} $")
col_stats[1].metric("VICTOIRES", st.session_state.stats['victoires'])
col_stats[2].metric("NIVEAU MARTINGALE", st.session_state.stats['martingale'])

# --- GRAPHE ÉPINGLÉ EN HAUT ---
st.subheader("📊 Analyse du Marché en Temps Réel")
placeholder_graphe = st.empty()

# --- CONFIGURATION LATÉRALE ---
st.sidebar.header("PARAMÈTRES DE PRODUCTION")
jeton_api = st.sidebar.text_input("Jeton API Deriv", type="password")

# Marchés sans abréviations
liste_marches = [
    "Volatility 10 Index", 
    "Volatility 25 Index", 
    "Volatility 50 Index", 
    "Volatility 75 Index", 
    "Volatility 100 Index",
    "Volatility 10 (1s) Index",
    "Volatility 25 (1s) Index"
]
marche = st.sidebar.selectbox("Sélectionnez le Marché", liste_marches)

# --- MOTEUR DU BOT ---
async def lancer_production():
    # Simulation de données haute fréquence
    data = pd.DataFrame({'close': [1250.0] * 30})
    while True:
        # Mise à jour du graphique (Dark Mode)
        fig = go.Figure(go.Scatter(y=data['close'], mode='lines', line=dict(color='#00ff88', width=3)))
        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=20, b=20))
        
        placeholder_graphe.plotly_chart(fig, use_container_width=True, key="kasaa_pro_chart")
        
        # Exécution de la stratégie
        await executer_ordre_automatique(None, marche, "ACTIF", data)
        await asyncio.sleep(1)

if st.sidebar.button("DÉMARRER LE TRADING"):
    if jeton_api:
        st.success(f"Production lancée sur {marche}")
        asyncio.run(lancer_production())
    else:
        st.warning("Veuillez entrer votre Jeton API pour sécuriser l'accès.")

# --- JOURNAL ---
st.subheader("📜 Journal de Trading (Haute Précision)")
if st.session_state.stats['logs']:
    st.table(pd.DataFrame(st.session_state.stats['logs']))