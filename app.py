import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- 1. CONFIGURATION ET STYLE ---
st.set_page_config(page_title="ARCHITECTE PRO - FINAL", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000; }
    header { visibility: hidden; }
    .user-card { background: #111; padding: 15px; border-radius: 12px; border: 1px solid #222; border-left: 5px solid #00ffbb; }
    .stat-label { color: #00ffbb; font-size: 10px; font-weight: bold; }
    .stat-value { color: #fff; font-size: 16px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALISATION DES VARIABLES (CRUCIAL) ---
if 'candles' not in st.session_state:
    st.session_state.candles = []
if 'stats' not in st.session_state:
    st.session_state.stats = {'mises': 0, 'gains': 0, 'pertes': 0, 'profit': 0.0, 'logs': []}
if 'last_trade_time' not in st.session_state:
    st.session_state.last_trade_time = 0

# --- 3. CATALOGUE ---
market_catalog = {
    "VOLATILITY (S)": {"Volat 10 (1s)": "1HZ10V", "Volat 25 (1s)": "1HZ25V", "Volat 50 (1s)": "1HZ50V", "Volat 100 (1s)": "1HZ100V"},
    "CRASH & BOOM": {"Crash 300": "C_300", "Boom 300": "B_300", "Crash 500": "C_500", "Boom 500": "B_500"}
}

# --- 4. BARRE LATÉRALE ---
with st.sidebar:
    st.title("🔐 CONFIGURATION")
    token = st.text_input("TON JETON API", type="password")
    cat_choisie = st.selectbox("CATÉGORIE", list(market_catalog.keys()))
    nom_marche = st.selectbox("MARCHÉ", list(market_catalog[cat_choisie].keys()))
    symbole = market_catalog[cat_choisie][nom_marche]
    lancer = st.button("🚀 ACTIVER LE FLUX")

# --- 5. LOGIQUE TECHNIQUE ---
def get_expert_advice(df):
    if len(df) < 5: return "Analyse...", "Collecte de données..."
    last = df.iloc[-1]
    is_bullish = last['close'] > last['open']
    body = abs(last['close'] - last['open'])
    wick = (last['high'] - max(last['close'], last['open'])) + (min(last['close'], last['open']) - last['low'])
    if not is_bullish and body > wick * 1.5: return "🚨 PRESSION VENDEUSE", "Forte baisse."
    if is_bullish and body > wick * 1.5: return "🔥 MOMENTUM HAUSSIER", "Forte hausse."
    return "⚖️ INDÉCISION", "Attente."

# --- 6. CRÉATION DE L'INTERFACE (LES BOÎTES) ---
c_info, c_graph = st.columns([1, 3])

with c_info:
    user_area = st.empty()
    st.markdown("### 📊 PERFORMANCE LIVE")
    perf_container = st.container() # Pour les metrics
    
    st.markdown("---")
    advice_area = st.empty()
    st.markdown("### 📜 HISTORIQUE")
    history_area = st.empty()

with c_graph:
    chart_area = st.empty()

# --- 7. FONCTIONS DE DESSIN ---
def update_ui_elements():
    s = st.session_state.stats
    with perf_container:
        col1, col2 = st.columns(2)
        col1.metric("MISES", f"{s['mises']}$")
        col1.metric("GAGNÉS", f"✅ {s['gains']}")
        col2.metric("PROFIT", f"{s['profit']}$")
        col2.metric("PERDUS", f"❌ {s['pertes']}")
    
    if s['logs']:
        history_area.table(pd.DataFrame(s['logs']).head(10))

def draw_all(df):
    if df.empty: return
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    status, detail = get_expert_advice(df)
    
    # Signal couleur
    color = "#00ffbb" if "HAUSSIER" in status else "#ff3333" if "VENDEUSE" in status else "#f1c40f"
    advice_area.markdown(f'<div style="border:2px solid {color};padding:15px;border-radius:12px;background:#0d1117;"><p style="color:{color};font-size:18px;font-weight:bold;margin:0;">{status}</p><p style="color:#bbb;font-size:12px;">{detail}</p></div>', unsafe_allow_html=True)

    # Graphique
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], increasing_line_color='#00ffbb', decreasing_line_color='#ff3333'))
    fig.add_trace(go.Scatter(x=df['time'], y=df['ema20'], line=dict(color='#ffcc00', width=1.5), name="EMA 20"))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=80,b=30,t=10), xaxis_rangeslider_visible=False)
    chart_area.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")
    update_ui_elements()

# --- 8. MOTEUR ASYNC ---
async def start_expert_bot():
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"authorize": token}))
        res = json.loads(await ws.recv())
        if "error" in res:
            st.error("Jeton invalide"); return

        u = res['authorize']
        user_area.markdown(f'<div class="user-card"><p class="stat-label">TRADER</p><p class="stat-value">{u["fullname"]}</p><p class="stat-label">SOLDE</p><p class="stat-value">{u["balance"]} {u["currency"]}</p></div>', unsafe_allow_html=True)
        
        await ws.send(json.dumps({"ticks_history": symbole, "subscribe": 1, "end": "latest", "count": 80, "style": "candles"}))
        
        while True:
            msg = json.loads(await ws.recv())
            if "ohlc" in msg:
                c = msg['ohlc']
                new_c = {'time': datetime.fromtimestamp(int(c['open_time'])), 'open': float(c['open']), 'high': float(c['high']), 'low': float(c['low']), 'close': float(c['close'])}
                
                if st.session_state.candles and st.session_state.candles[-1]['time'] == new_c['time']:
                    st.session_state.candles[-1] = new_c
                else:
                    st.session_state.candles.append(new_c)
                    if len(st.session_state.candles) > 80: st.session_state.candles.pop(0)
                
                df_actuel = pd.DataFrame(st.session_state.candles)
                status, _ = get_expert_advice(df_actuel)
                
                # APPEL DU BOT DE TRADE
                from bot_test import executer_ordre_automatique
                await executer_ordre_automatique(ws, symbole, status, df_actuel)
                
                draw_all(df_actuel)
            await asyncio.sleep(0.01)

if lancer and token:
    asyncio.run(start_expert_bot())