import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- 1. CONFIGURATION & DESIGN CYBERPUNK ---
st.set_page_config(page_title="KASAA TRADE PRO", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* FOND NOIR AVEC EFFET MULTICOLORE ANIMÉ */
    .stApp {
        background: linear-gradient(125deg, #000000, #0a0a0a, #001f1f, #1a001a);
        background-size: 400% 400%;
        animation: gradientAnimation 15s ease infinite;
        color: white;
    }

    @keyframes gradientAnimation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* HEADER FIXE */
    .fixed-header {
        position: sticky;
        top: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 1000;
        padding: 10px;
        border-bottom: 1px solid #333;
    }

    /* CARTES DE STATS NÉON */
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #444;
        text-align: center;
        transition: 0.3s;
    }
    .stat-card:hover { border-color: #00ffbb; box-shadow: 0 0 10px #00ffbb; }
    
    .label { color: #aaa; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .value { color: #fff; font-size: 22px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALISATION ---
if 'candles' not in st.session_state:
    st.session_state.candles = []
if 'stats' not in st.session_state:
    st.session_state.stats = {'gains': 0, 'pertes': 0, 'somme_gains': 0.0, 'somme_pertes': 0.0, 'profit': 0.0, 'logs': []}

# --- 3. INTERFACE FIGÉE ---
header = st.container()
with header:
    st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
    
    # Infos Utilisateur
    user_area = st.empty()
    
    # Graphique (Hauteur fixe pour mobile/PC)
    chart_area = st.empty()
    
    # Les 4 Stats
    s1, s2, s3, s4 = st.columns(4)
    st1 = s1.empty()
    st2 = s2.empty()
    st3 = s3.empty()
    st4 = s4.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# Zone défilante (Historique)
st.markdown("### 📜 HISTORIQUE LIVE")
history_area = st.empty()

# --- 4. MISE À JOUR LIVE ---
def update_ui(df):
    s = st.session_state.stats
    
    # Update Stats
    st1.markdown(f'<div class="stat-card"><p class="label">✅ Gains</p><p class="value" style="color:#00ffbb">{s["gains"]}</p></div>', unsafe_allow_html=True)
    st2.markdown(f'<div class="stat-card"><p class="label">❌ Pertes</p><p class="value" style="color:#ff3333">{s["pertes"]}</p></div>', unsafe_allow_html=True)
    st3.markdown(f'<div class="stat-card"><p class="label">💰 Encaissé</p><p class="value">+{s["somme_gains"]:.2f}$</p></div>', unsafe_allow_html=True)
    st4.markdown(f'<div class="stat-card"><p class="label">📉 Perdu</p><p class="value">-{s["somme_pertes"]:.2f}$</p></div>', unsafe_allow_html=True)

    # Update Graphique (Plotly Dark)
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='#00ffbb', decreasing_line_color='#ff3333'
    )])
    fig.update_layout(
        template="plotly_dark", 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        height=350, 
        margin=dict(l=0,r=10,b=0,t=0), 
        xaxis_rangeslider_visible=False
    )
    chart_area.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    if s['logs']:
        history_area.dataframe(pd.DataFrame(s['logs']), use_container_width=True)

# --- 5. LOGIQUE ASYNC (MOTEUR) ---
async def start_engine(token, market):
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"authorize": token}))
        res = json.loads(await ws.recv())
        
        if "error" in res:
            st.error("Token invalide !"); return

        u = res['authorize']
        user_area.markdown(f"🟢 **{u['fullname']}** | Solde : `{u['balance']} {u['currency']}`")
        
        # Souscription au marché
        await ws.send(json.dumps({
            "ticks_history": market, "subscribe": 1, "end": "latest", 
            "count": 50, "style": "candles", "granularity": 60
        }))

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
                
                update_ui(pd.DataFrame(st.session_state.candles))
            await asyncio.sleep(0.1)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛠️ KASAÃ SETTINGS")
    t = st.text_input("API TOKEN", type="password")
    m = st.selectbox("MARCHÉ", ["1HZ10V", "1HZ50V", "C_300", "B_300", "1HZ100V"])
    btn = st.button("ACTIVER LE FLUX")

if btn and t:
    asyncio.run(start_engine(t, m))