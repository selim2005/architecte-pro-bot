import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
import asyncio
from datetime import datetime

# --- CONFIGURATION ÉLÉGANTE ---
st.set_page_config(page_title="KASAA TRADE PRO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c1f26; padding: 15px; border-radius: 10px; border: 1px solid #00ff88; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
if 'stats' not in st.session_state:
    st.session_state.stats = {'profit': 0.0, 'wins': 0, 'loss': 0, 'martingale': 0, 'logs': []}

# --- BARRE LATÉRALE ---
st.sidebar.title("🛠️ PARAMÈTRES")
token = st.sidebar.text_input("Jeton API Deriv", type="password")
marche_complet = st.sidebar.selectbox("Marché de Production", [
    "Volatility 10 Index", "Volatility 25 Index", "Volatility 50 Index", 
    "Volatility 75 Index", "Volatility 100 Index", "Volatility 10 (1s) Index", "Volatility 100 (1s) Index"
])
mise_base = st.sidebar.number_input("Mise de base ($)", value=10.0)

# --- DASHBOARD DE HAUT DE PAGE ---
st.title("💎 KASAA TRADE - L'Architecte Pro")
c1, c2, c3 = st.columns(3)
c1.metric("PROFIT NET", f"{st.session_state.stats['profit']:.2f} $")
c2.metric("VICTOIRES", st.session_state.stats['wins'])
c3.metric("NIVEAU MARTINGALE", st.session_state.stats['martingale'])

# --- ZONE GRAPHIQUE ÉPINGLÉE ---
st.subheader(f"📊 Analyse Directe : {marche_complet}")
graph_container = st.empty() # C'est ici qu'on évite l'erreur DuplicateKey

# --- LOGIQUE DE TRADING ET MOTEUR ---
async def start_trading():
    prices = [1250.0] * 50
    while True:
        # Simulation/Récupération prix
        new_price = prices[-1] + (pd.Series([1, -1]).sample().values[0] * 0.5)
        prices.append(new_price)
        df = pd.DataFrame(prices[-50:], columns=['close'])
        
        # Calcul RSI pour rentabilité
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1] if not df['rsi'].empty else 50
        
        # Mise à jour du Graphe (Sans erreur de clé)
        fig = go.Figure(go.Scatter(y=df['close'], mode='lines', line=dict(color='#00ff88', width=2)))
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
        graph_container.plotly_chart(fig, use_container_width=True, key="live_kasaa_chart")

        # Décision Trading
        if current_rsi < 30 or current_rsi > 70:
            type_ordre = "ACHAT (CALL)" if current_rsi < 30 else "VENTE (PUT)"
            current_stake = mise_base * (2 ** st.session_state.stats['martingale'])
            
            # Simulation résultat (À lier à l'API plus tard)
            win = current_rsi < 35 if current_rsi < 30 else current_rsi > 65
            
            if win:
                st.session_state.stats['profit'] += current_stake * 0.95
                st.session_state.stats['wins'] += 1
                st.session_state.stats['martingale'] = 0
                res = "✅ GAGNÉ"
            else:
                st.session_state.stats['profit'] -= current_stake
                st.session_state.stats['loss'] += 1
                st.session_state.stats['martingale'] += 1
                res = "❌ PERDU"

            st.session_state.stats['logs'].insert(0, {
                "Heure": datetime.now().strftime("%H:%M:%S"),
                "Marché": marche_complet,
                "RSI": round(current_rsi, 2),
                "Action": type_ordre,
                "Mise": f"{current_stake}$",
                "Résultat": res
            })

        await asyncio.sleep(1)

if st.sidebar.button("🚀 LANCER LA PRODUCTION"):
    if token:
        asyncio.run(start_trading())
    else:
        st.sidebar.error("⚠️ Token manquant")

# --- LOGS EN BAS ---
st.subheader("📜 Journal de Trading")
if st.session_state.stats['logs']:
    st.table(pd.DataFrame(st.session_state.stats['logs']))