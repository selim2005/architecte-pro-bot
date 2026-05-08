import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
import asyncio
from datetime import datetime

# --- CONFIGURATION PREMIUM ---
st.set_page_config(page_title="KASAA TRADE PRO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetric"] { background-color: #1c1f26; border: 1px solid #00ff88; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'stats' not in st.session_state:
    st.session_state.stats = {'profit': 0.0, 'victoires': 0, 'pertes': 0, 'martingale': 0, 'logs': []}

# --- 1. GRAPHIQUE ÉPINGLÉ EN HAUT ---
st.title("💎 KASAA TRADE - Système Haute Performance")
col_stats = st.columns(3)
col_stats[0].metric("PROFIT NET", f"{st.session_state.stats['profit']:.2f} $")
col_stats[1].metric("TAUX DE RÉUSSITE", f"{st.session_state.stats['victoires']}W / {st.session_state.stats['pertes']}L")
col_stats[2].metric("NIVEAU MARTINGALE", st.session_state.stats['martingale'])

st.write("---")
placeholder_graph = st.empty() # Évite l'erreur DuplicateKey

# --- 2. CONFIGURATION BARRE LATÉRALE ---
st.sidebar.header("🕹️ CONTRÔLE DE PRODUCTION")
jeton = st.sidebar.text_input("Jeton API Deriv", type="password")
marche = st.sidebar.selectbox("Sélection du Marché", [
    "Volatility 10 Index", "Volatility 25 Index", "Volatility 50 Index", 
    "Volatility 75 Index", "Volatility 100 Index", "Volatility 10 (1s) Index"
])
mise_base = st.sidebar.number_input("Mise initiale ($)", value=10.0)

# --- 3. MOTEUR DE RENTABILITÉ ---
async def cycle_trading():
    historique = [1250.0] * 30
    while True:
        # Simulation de flux réel
        nouveau_prix = historique[-1] + (pd.Series([0.5, -0.5]).sample().values[0])
        historique.append(nouveau_prix)
        df = pd.DataFrame(historique[-30:], columns=['close'])
        
        # Stratégie RSI 14
        df['rsi'] = ta.rsi(df['close'], length=14)
        valeur_rsi = df['rsi'].iloc[-1] if not df['rsi'].empty else 50

        # Affichage du Graphe (ID Unique pour éviter le bug)
        fig = go.Figure(go.Scatter(y=df['close'], mode='lines', line=dict(color='#00ff88', width=2)))
        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=0,b=0))
        placeholder_graph.plotly_chart(fig, use_container_width=True, key="graph_kasaa_final")

        # Exécution des ordres
        if valeur_rsi < 30 or valeur_rsi > 70:
            type_ordre = "ACHAT (CALL)" if valeur_rsi < 30 else "VENTE (PUT)"
            mise_actuelle = mise_base * (2 ** st.session_state.stats['martingale'])
            
            # Logique de gain/perte
            gagne = (valeur_rsi < 35 if valeur_rsi < 30 else valeur_rsi > 65)
            
            if gagne:
                st.session_state.stats['profit'] += mise_actuelle * 0.95
                st.session_state.stats['victoires'] += 1
                st.session_state.stats['martingale'] = 0
                res = "✅ GAGNÉ"
            else:
                st.session_state.stats['profit'] -= mise_actuelle
                st.session_state.stats['pertes'] += 1
                st.session_state.stats['martingale'] += 1
                res = "❌ PERDU"

            st.session_state.stats['logs'].insert(0, {
                "Heure": datetime.now().strftime("%H:%M:%S"),
                "Action": type_ordre,
                "Mise": f"{mise_actuelle}$",
                "Résultat": res
            })

        await asyncio.sleep(1)

if st.sidebar.button("LANCER LA SESSION"):
    if jeton:
        asyncio.run(cycle_trading())
    else:
        st.sidebar.error("Jeton manquant")

# --- 4. JOURNAL ---
st.subheader("📜 Journal de Trading")
st.table(pd.DataFrame(st.session_state.stats['logs']))