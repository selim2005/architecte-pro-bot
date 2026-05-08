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
    .value { font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INITIALISATION DES VARIABLES ---
if 'stats' not in st.session_state:
    st.session_state.stats = {'gains': 0, 'pertes': 0, 'somme_gains': 0.0, 'somme_pertes': 0.0, 'logs': []}
if 'candles' not in st.session_state:
    st.session_state.candles = []

# --- 4. INTERFACE FIXE ---
header = st.container()
with header:
    # On utilise des placeholders (.empty()) pour éviter l'erreur DuplicateElementId
    user_info = st.empty()
    chart_area = st.empty()
    c1, c2, c3, c4 = st.columns(4)
    st1, st2, st3, st4 = c1.empty(), c2.empty(), c3.empty(), c4.empty()
    st.markdown("---")

history_area = st.empty()

# --- 5. LOGIQUE DE TRADING AUTOMATIQUE ---
def executer_strategie(df):
    s = st.session_state.stats
    last_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    
    # Stratégie simple : On suit la tendance de la dernière bougie
    type_trade = "CALL" if last_close > prev_close else "PUT"
    resultat = "GAGNÉ" if (type_trade == "CALL" and last_close > prev_close) else "PERDU"
    
    mise = 10.0
    profit = mise * 0.95 if resultat == "GAGNÉ" else -mise
    
    # Mise à jour des compteurs
    if resultat == "GAGNÉ":
        s['gains'] += 1
        s['somme_gains'] += profit
    else:
        s['pertes'] += 1
        s['somme_pertes'] += abs(profit)
    
    # Enregistrement
    s['logs'].insert(0, {
        "Heure": datetime.now().strftime("%H:%M:%S"),
        "Type": type_trade,
        "Mise": f"{mise}$",
        "Résultat": resultat,
        "Profit": f"{profit:.2f}$"
    })

# --- 6. MOTEUR TEMPS RÉEL ET TOUS LES MARCHÉS ---
async def start_trading(token, market):
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"authorize": token}))
        auth_res = json.loads(await ws.recv())
        
        if "error" in auth_res:
            st.error("Erreur Token !"); return

        user_info.info(f"SOLDE : {auth_res['authorize']['balance']} $")

        # Souscription
        await ws.send(json.dumps({
            "ticks_history": market, "subscribe": 1, "end": "latest",
            "count": 50, "style": "candles", "granularity": 60
        }))

        while True:
            msg = json.loads(await ws.recv())
            if "ohlc" in msg:
                c = msg['ohlc']
                new_c = {'time': datetime.fromtimestamp(int(c['open_time'])), 'open': float(c['open']), 'high': float(c['high']), 'low': float(c['low']), 'close': float(c['close'])}
                
                # Mise à jour bougies
                if st.session_state.candles and st.session_state.candles[-1]['time'] == new_c['time']:
                    st.session_state.candles[-1] = new_c
                else:
                    st.session_state.candles.append(new_c)
                    if len(st.session_state.candles) > 1:
                        executer_strategie(pd.DataFrame(st.session_state.candles))
                
                # Affichage
                df = pd.DataFrame(st.session_state.candles)
                st1.markdown(f'<div class="stat-card"><p class="value" style="color:#00ffbb">{s["gains"]}</p></div>', unsafe_allow_html=True)
                # ... (Répéter pour st2, st3, st4)
                
                fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
                fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                chart_area.plotly_chart(fig, use_container_width=True, key=f"chart_{market}")
                
                if s['logs']: history_area.dataframe(pd.DataFrame(s['logs']), use_container_width=True)
            
            await asyncio.sleep(0.5)

# --- SIDEBAR (LISTE DE TOUS LES MARCHÉS) ---
with st.sidebar:
    st.header("KASAA CONTROL")
    t = st.text_input("TOKEN", type="password")
    # Ajout de tous les marchés principaux
    m = st.selectbox("MARCHÉ", [
        "R_10", "R_25", "R_50", "R_75", "R_100", # Volatility
        "1HZ10V", "1HZ50V", "1HZ100V",           # Volatility (1s)
        "B_300", "B_500", "B_1000",              # Boom
        "C_300", "C_500", "C_1000",              # Crash
        "JD10", "JD25", "JD50"                   # Jump
    ])
    run = st.button("LANCER LE TRADING")

if run and t:
    asyncio.run(start_trading(t, m))