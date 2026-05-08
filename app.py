import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="KASAA TRADE PRO", layout="wide", initial_sidebar_state="collapsed")

# --- DESIGN FIXE & RESPONSIVE ---
st.markdown("""
    <style>
    .main { background-color: #06090F; }
    header { visibility: hidden; }
    
    /* Zone du haut qui ne bouge pas */
    .fixed-header {
        position: sticky;
        top: 0;
        background-color: #06090F;
        z-index: 1000;
        padding-bottom: 10px;
        border-bottom: 1px solid #1c2128;
    }
    
    .stat-card {
        background: #161B22;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #30363D;
        text-align: center;
    }
    .label { color: #8B949E; font-size: 10px; text-transform: uppercase; }
    .value { color: #FFFFFF; font-size: 18px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
if 'candles' not in st.session_state:
    st.session_state.candles = []
if 'stats' not in st.session_state:
    st.session_state.stats = {'mises': 0, 'gains': 0, 'pertes': 0, 'profit': 0.0, 'somme_gains': 0.0, 'somme_pertes': 0.0, 'logs': []}

# --- INTERFACE ---
header_zone = st.container()
with header_zone:
    # 1. Infos Utilisateur
    user_area = st.empty()
    
    # 2. Graphique fixe
    chart_area = st.empty()
    
    # 3. Les 4 colonnes de stats
    c1, c2, c3, c4 = st.columns(4)
    stat1 = c1.empty()
    stat2 = c2.empty()
    stat3 = c3.empty()
    stat4 = c4.empty()
    st.markdown("---")

# Zone défilante
history_area = st.empty()

# --- FONCTION DE MISE À JOUR ---
def update_dashboard(df):
    s = st.session_state.stats
    
    # Update Stats
    stat1.markdown(f'<div class="stat-card"><p class="label">✅ Gains</p><p class="value" style="color:#238636">{s["gains"]}</p></div>', unsafe_allow_html=True)
    stat2.markdown(f'<div class="stat-card"><p class="label">❌ Pertes</p><p class="value" style="color:#F85149">{s["pertes"]}</p></div>', unsafe_allow_html=True)
    stat3.markdown(f'<div class="stat-card"><p class="label">💰 Encaissé</p><p class="value">+{s["somme_gains"]:.1f}$</p></div>', unsafe_allow_html=True)
    stat4.markdown(f'<div class="stat-card"><p class="label">📉 Perdu</p><p class="value">-{s["somme_pertes"]:.1f}$</p></div>', unsafe_allow_html=True)

    # Update Graph (Bougies qui bougent)
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='#00ffbb', decreasing_line_color='#ff3333'
    )])
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=10,b=0,t=0), xaxis_rangeslider_visible=False)
    chart_area.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    if s['logs']:
        history_area.table(pd.DataFrame(s['logs']).head(10))

# --- MOTEUR WEBSOCKET ---
async def connect_to_market(token, market_code):
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        # 1. Connexion
        await ws.send(json.dumps({"authorize": token}))
        res = json.loads(await ws.recv())
        
        if "error" in res:
            st.error("Token Invalide")
            return

        user_area.success(f"Connecté : {res['authorize']['fullname']} | Solde : {res['authorize']['balance']} $")
        
        # 2. Souscription au Marché (Flux de bougies 1 minute)
        await ws.send(json.dumps({
            "ticks_history": market_code,
            "subscribe": 1,
            "end": "latest",
            "count": 50,
            "style": "candles",
            "granularity": 60
        }))

        while True:
            msg = json.loads(await ws.recv())
            if "ohlc" in msg:
                c = msg['ohlc']
                new_candle = {
                    'time': datetime.fromtimestamp(int(c['open_time'])),
                    'open': float(c['open']), 'high': float(c['high']), 
                    'low': float(c['low']), 'close': float(c['close'])
                }
                
                # Mise à jour de la liste
                if st.session_state.candles and st.session_state.candles[-1]['time'] == new_candle['time']:
                    st.session_state.candles[-1] = new_candle
                else:
                    st.session_state.candles.append(new_candle)
                    if len(st.session_state.candles) > 50: st.session_state.candles.pop(0)
                
                df = pd.DataFrame(st.session_state.candles)
                update_dashboard(df)
            
            await asyncio.sleep(0.1)

# --- SIDEBAR ---
with st.sidebar:
    st.title("CONFIG")
    user_token = st.text_input("TOKEN API", type="password")
    selected_market = st.selectbox("CHOISIR MARCHÉ", ["1HZ10V", "1HZ50V", "1HZ100V", "C_300", "B_300"])
    start_btn = st.button("LANCER LE FLUX LIVE")

if start_btn and user_token:
    asyncio.run(connect_to_market(user_token, selected_market))