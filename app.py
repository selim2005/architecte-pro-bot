import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="KASAA TRADE PRO", layout="wide")

# --- 2. STYLE CYBERPUNK ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(125deg, #000, #050505, #001a1a); color: white; }
    .stat-card { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border: 1px solid #444; text-align: center; }
    .label { color: #8B949E; font-size: 10px; text-transform: uppercase; }
    .value { font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INITIALISATION DES VARIABLES ---
if 'stats' not in st.session_state:
    st.session_state.stats = {'gains': 0, 'pertes': 0, 'somme_gains': 0.0, 'somme_pertes': 0.0, 'logs': []}
if 'candles' not in st.session_state:
    st.session_state.candles = []

# --- 4. INTERFACE ---
user_info = st.empty()
chart_area = st.empty()
c1, c2, c3, c4 = st.columns(4)
st1, st2, st3, st4 = c1.empty(), c2.empty(), c3.empty(), c4.empty()
st.markdown("---")
history_area = st.empty()

# --- 5. LOGIQUE DE TRADING ---
def executer_trade(df):
    s = st.session_state.stats
    close_p = df['close'].iloc[-1]
    open_p = df['open'].iloc[-1]
    
    # Stratégie : Si bougie actuelle est plus haute que son ouverture
    resultat = "GAGNÉ" if close_p > open_p else "PERDU"
    mise = 10.0
    profit = mise * 0.95 if resultat == "GAGNÉ" else -mise
    
    if resultat == "GAGNÉ":
        s['gains'] += 1
        s['somme_gains'] += profit
    else:
        s['pertes'] += 1
        s['somme_pertes'] += abs(profit)
    
    s['logs'].insert(0, {
        "Heure": datetime.now().strftime("%H:%M:%S"),
        "Résultat": resultat,
        "Profit": f"{profit:.2f}$"
    })

# --- 6. MOTEUR TEMPS RÉEL ---
async def start_trading(token, market):
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"authorize": token}))
        auth = json.loads(await ws.recv())
        if "error" in auth:
            st.error("Token Invalide"); return
        
        user_info.success(f"Connecté : {auth['authorize']['fullname']} | Solde : {auth['authorize']['balance']}$")

        await ws.send(json.dumps({
            "ticks_history": market, "subscribe": 1, "end": "latest",
            "count": 50, "style": "candles", "granularity": 60
        }))

        while True:
            msg = json.loads(await ws.recv())
            if "ohlc" in msg:
                c = msg['ohlc']
                new_candle = {'time': datetime.fromtimestamp(int(c['open_time'])), 'open': float(c['open']), 'high': float(c['high']), 'low': float(c['low']), 'close': float(c['close'])}
                
                if st.session_state.candles and st.session_state.candles[-1]['time'] == new_candle['time']:
                    st.session_state.candles[-1] = new_candle
                else:
                    st.session_state.candles.append(new_candle)
                    if len(st.session_state.candles) > 1:
                        executer_trade(pd.DataFrame(st.session_state.candles))
                
                # Mise à jour de l'affichage (Variable 's' définie ici)
                s = st.session_state.stats
                st1.markdown(f'<div class="stat-card"><p class="label">✅ Gains</p><p class="value" style="color:#00ffbb">{s["gains"]}</p></div>', unsafe_allow_html=True)
                st2.markdown(f'<div class="stat-card"><p class="label">❌ Pertes</p><p class="value" style="color:#ff3333">{s["pertes"]}</p></div>', unsafe_allow_html=True)
                st3.markdown(f'<div class="stat-card"><p class="label">💰 Encaissé</p><p class="value">+{s["somme_gains"]:.1f}$</p></div>', unsafe_allow_html=True)
                st4.markdown(f'<div class="stat-card"><p class="label">📉 Perdu</p><p class="value">-{s["somme_pertes"]:.1f}$</p></div>', unsafe_allow_html=True)

                fig = go.Figure(data=[go.Candlestick(x=pd.DataFrame(st.session_state.candles)['time'], open=pd.DataFrame(st.session_state.candles)['open'], high=pd.DataFrame(st.session_state.candles)['high'], low=pd.DataFrame(st.session_state.candles)['low'], close=pd.DataFrame(st.session_state.candles)['close'])])
                fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                chart_area.plotly_chart(fig, use_container_width=True, key=f"kasaa_{market}")
                
                if s['logs']: history_area.dataframe(pd.DataFrame(s['logs']), use_container_width=True)
            await asyncio.sleep(0.2)

# --- SIDEBAR (TOUS LES MARCHÉS) ---
with st.sidebar:
    st.title("KASAA CONFIG")
    t = st.text_input("TOKEN API", type="password")
    m = st.selectbox("MARCHÉ", [
        "R_10", "R_25", "R_50", "R_75", "R_100", 
        "1HZ10V", "1HZ50V", "1HZ100V", 
        "B_300", "B_500", "B_1000", 
        "C_300", "C_500", "C_1000"
    ])
    btn = st.button("LANCER LE TRADING LIVE")

if btn and t:
    asyncio.run(start_trading(t, m))