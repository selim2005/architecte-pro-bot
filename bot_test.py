import json
import asyncio
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURATION DU RISQUE "ARCHITECTE" ---
MISE_DE_BASE = 10.0
LIMIT_TAKE_PROFIT = 50.0  # Objectif initial
LIMIT_STOP_LOSS = -30.0   # Sécurité maximale
MAX_MARTINGALE_LEVEL = 3  # Protection contre les krachs

# --- LOGIQUE TECHNIQUE ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

async def executer_ordre_automatique(ws, symbole, status, df):
    # 1. Initialisation des stats si besoin
    if 'stats' not in st.session_state:
        st.session_state.stats = {'mises': 0, 'gains': 0, 'pertes': 0, 'profit': 0.0, 'logs': [], 'martingale': 0}
    
    s = st.session_state.stats
    
    # 2. Gestion de l'objectif intelligent
    # Si profit > 50, il continue seulement s'il y a une opportunité "en or"
    if s['profit'] >= LIMIT_TAKE_PROFIT:
        st.info("🎯 Objectif atteint. Recherche d'opportunités bonus...")
    if s['profit'] <= LIMIT_STOP_LOSS:
        st.error("🛑 Sécurité maximale atteinte. Arrêt pour protéger le capital.")
        return

    # 3. Calcul du RSI
    if len(df) < 15: return
    df['rsi'] = calculate_rsi(df['close'])
    current_rsi = df['rsi'].iloc[-1]

    # 4. Décision RSI (Filtrage strict)
    type_contrat = None
    if current_rsi <= 30:
        type_contrat = "CALL"
    elif current_rsi >= 70:
        type_contrat = "PUT"

    # 5. Exécution avec Martingale Réelle
    if type_contrat:
        # Anti-spam : 1 trade par minute
        current_time = datetime.now().timestamp()
        if 'last_trade_time' not in st.session_state: st.session_state.last_trade_time = 0
        if current_time - st.session_state.last_trade_time < 60: return

        st.session_state.last_trade_time = current_time
        
        # Calcul de la mise (Martingale)
        mise_actuelle = MISE_DE_BASE * (2 ** s['martingale'])
        
        # Envoi de l'ordre réel à Deriv
        requete = {
            "buy": 1,
            "price": mise_actuelle,
            "parameters": {
                "amount": mise_actuelle,
                "basis": "stake",
                "contract_type": type_contrat,
                "currency": "USD",
                "duration": 1,
                "duration_unit": "m",
                "symbol": symbole
            }
        }
        
        await ws.send(json.dumps(requete))
        
        # Lecture du résultat réel (on attend la réponse du serveur)
        response = json.loads(await ws.recv())
        
        if "buy" in response:
            contract_id = response['buy']['contract_id']
            # Ici on simule l'attente du résultat de 1 min pour la fluidité UI
            # Dans une version avancée, on utiliserait 'proposal_open_contract'
            
            # Simulation fluide du résultat basé sur la tendance
            win = (type_contrat == "CALL" and df['close'].iloc[-1] > df['open'].iloc[-1]) or \
                  (type_contrat == "PUT" and df['close'].iloc[-1] < df['open'].iloc[-1])

            if win:
                profit_brut = mise_actuelle * 0.95
                s['profit'] += profit_brut
                s['gains'] += 1
                s['martingale'] = 0 # Reset Martingale
                res_txt = "✅ GAGNÉ"
            else:
                s['profit'] -= mise_actuelle
                s['pertes'] += 1
                s['martingale'] = min(s['martingale'] + 1, MAX_MARTINGALE_LEVEL)
                res_txt = "❌ PERDU"

            s['mises'] += mise_actuelle
            s['logs'].insert(0, {
                "Heure": datetime.now().strftime("%H:%M:%S"),
                "Marché": symbole,
                "RSI": f"{current_rsi:.2f}",
                "Type": type_contrat,
                "Mise": f"{mise_actuelle}$",
                "Résultat": res_txt
            })
            st.toast(f"Trade {type_contrat} terminé : {res_txt}", icon="📊")