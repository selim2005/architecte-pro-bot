import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- 1. CONFIGURATION ET LOOK PREMIUM ---
st.set_page_config(page_title="KASAA TRADE - ARCHITECTE PRO", layout="wide")

st.markdown("""
    <style>
    /* FOND NOIR ET STYLE GENERAL */
    .main { background-color: #06090F; }
    header { visibility: hidden; }
    
    /* FIXER LE GRAPHIQUE ET LES INFOS (STICKY) */
    .sticky-container {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        background-color: #06090F;
        z-index: 1000;
        padding-bottom: 10px;
        border-bottom: 2px solid #1c2128;
    }
    
    /* CARTES DE STATISTIQUES LOOK PRO */
    .stat-card {
        background: #161B22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363D;
        text-align: center;
    }
    .label { color: #8B949E; font-size: 12px; text-transform: uppercase; }
    .value { color: #FFFFFF; font-size: 22px; font-weight: bold; }
    .gain-val { color: #238636; }
    .loss-val { color: #F85149; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALISATION ---
if 'candles' not in st.session_state:
    st.session_state.candles = []
if 'stats' not in st.session_state:
    # On ajoute somme_gains et somme_pertes pour le rapport détaillé
    st.session_state.stats = {
        'mises': 0, 'gains': 0, 'pertes': 0, 'profit': 0.0, 
        'somme_gains': 0.0, 'somme_pertes': 0.0, 'logs': []
    }

# --- 3. LOGIQUE TECHNIQUE (SIGNAL) ---
def get_expert_advice(df):
    if len(df) < 5: return "Analyse...", "Collecte de données..."
    last = df.iloc[-1]
    is_bullish = last['close'] > last['open']
    body = abs(last['close'] - last['open'])
    wick = (last['high'] - max(last['close'], last['open'])) + (min(last['close'], last['open']) - last['low'])
    if not is_bullish and body > wick * 1.5: return "🚨 PRESSION VENDEUSE", "Forte baisse."
    if is_bullish and body > wick * 1.5: return "🔥 MOMENTUM HAUSSIER", "Forte hausse."
    return "⚖️ INDÉCISION", "Attente."

# --- 4. BARRE LATÉRALE ---
with st.sidebar:
    st.title("🔐 KASAÃ CONFIG")
    token = st.text_input("TON JETON API", type="password")
    symbole = st.selectbox("MARCHÉ", ["1HZ10V", "1HZ25V", "1HZ50V", "1HZ100V", "C_300", "B_300"])
    lancer = st.button("🚀 LANCER LE BOT")

# --- 5. INTERFACE FIGÉE (HEADER) ---
# On crée un conteneur qui restera en haut
header_container = st.container()

with header_container:
    # Zone utilisateur (Nom et Solde)
    user_area = st.empty()
    
    # Graphique principal
    chart_area = st.empty()
    
    # Résumé des Performances (Les 4 colonnes demandées)
    st.markdown("### 📊 PERFORMANCE DE LA SESSION")
    p1, p2, p3, p4 = st.columns(4)
    stat_gains_count = p1.empty()
    stat_pertes_count = p2.empty()
    stat_somme_gains = p3.empty()
    stat_somme_pertes = p4.empty()
    
    # Verdict et Conseil
    st.markdown("---")
    advice_area = st.empty()

# --- 6. ZONE DÉFILANTE (HISTORIQUE) ---
st.markdown("### 📜 HISTORIQUE DES TRADES")
history_area = st.empty()

# --- 7. FONCTIONS DE DESSIN ---
def update_ui(df):
    s = st.session_state.stats
    
    # 1. Mise à jour des stats (Les colonnes que tu as demandées)
    stat_gains_count.markdown(f'<div class="stat-card"><p class="label">✅ Total Gains</p><p class="value gain-val">{s["gains"]}</p></div>', unsafe_allow_html=True)
    stat_pertes_count.markdown(f'<div class="stat-card"><p class="label">❌ Total Pertes</p><p class="value loss-val">{s["pertes"]}</p></div>', unsafe_allow_html=True)
    stat_somme_gains.markdown(f'<div class="stat-card"><p class="label">💰 Somme Gagnée</p><p class="value gain-val">+{s["somme_gains"]:.2f}$</p></div>', unsafe_allow_html=True)
    stat_somme_pertes.markdown(f'<div class="stat-card"><p class="label">📉 Somme Perdue</p><p class="value loss-val">-{s["somme_pertes"]:.2f}$</p></div>', unsafe_allow_html=True)
    
    # 2. Dessiner le graphique
    status, detail = get_expert_advice(df)
    color = "#00ffbb" if "HAUSSIER" in status else "#ff3333" if "VENDEUSE" in status else "#f1c40f"
    
    fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                                         increasing_line_color='#00ffbb', decreasing_line_color='#ff3333')])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=50,b=0,t=0), xaxis_rangeslider_visible=False)
    chart_area.plotly_chart(fig, use_container_width=True)
    
    # 3. Verdict Profit/Perte
    verdict = "✅ EN PROFIT" if s['profit'] > 0 else "❌ EN PERTE" if s['profit'] < 0 else "⚖️ ÉQUILIBRE"
    v_color = "#00ffbb" if s['profit'] > 0 else "#ff3333"
    advice_area.markdown(f'<div style="background:#161B22;padding:10px;border-radius:10px;border-left:5px solid {v_color}"><h3 style="margin:0;color:{v_color}">{verdict} ({s["profit"]:.2f}$)</h3><p style="color:#8B949E">{status} : {detail}</p></div>', unsafe_allow_html=True)

    # 4. Historique (Tableau)
    if s['logs']:
        history_area.table(pd.DataFrame(s['logs']))

# --- 8. MOTEUR ASYNC ---
async def start_expert_bot():
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"authorize": token}))
        res = json.loads(await ws.recv())
        if "error" in res:
            st.error("Jeton invalide"); return

        u = res['authorize']
        user_area.markdown(f'<div style="background:#111;padding:10px;border-radius:10px;border:1px solid #222"><p style="color:#00ffbb;margin:0">TRADER : <b>{u["fullname"]}</b> | SOLDE : <b>{u["balance"]} {u["currency"]}</b></p></div>', unsafe_allow_html=True)
        
        await ws.send(json.dumps({"ticks_history": symbole, "subscribe": 1, "end": "latest", "count": 50, "style": "candles"}))
        
        while True:
            msg = json.loads(await ws.recv())
            if "ohlc" in msg:
                c = msg['ohlc']
                new_c = {'time': datetime.fromtimestamp(int(c['open_time'])), 'open': float(c['open']), 'high': float(c['high']), 'low': float(c['low']), 'close': float(c['close'])}
                
                if st.session_state.candles and st.session_state.candles[-1]['time'] == new_c['time']:
                    st.session_state.candles[-1] = new_c
                else:
                    st.session_state.candles.append(new_c)
                    if len(st.session_state.candles) > 50: st.session_state.candles.pop(0)
                
                df_actuel = pd.DataFrame(st.session_state.candles)
                update_ui(df_actuel)
                
            await asyncio.sleep(0.1)

if lancer and token:
    asyncio.run(start_expert_bot())