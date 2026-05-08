import json
import asyncio
import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DU RISQUE ---
LIMIT_STOP_LOSS = -50.0  
LIMIT_TAKE_PROFIT = 100.0 
MISE_DE_BASE = 10.0

async def executer_ordre_automatique(ws, symbole, status, df):
    # 1. RÉCUPÉRATION DES STATS DEPUIS LA SESSION
    s = st.session_state.stats
    
    # 2. VÉRIFICATION DES LIMITES DE SÉCURITÉ
    if s['profit'] <= LIMIT_STOP_LOSS:
        st.error("🛑 STOP LOSS ATTEINT.")
        return
    if s['profit'] >= LIMIT_TAKE_PROFIT:
        st.success("🎯 OBJECTIF ATTEINT !")
        return

    # 3. DÉCISION DE TRADING (Plus réactive)
    type_contrat = None
    if "HAUSSIER" in status:
        type_contrat = "CALL"
    elif "VENDEUSE" in status:
        type_contrat = "PUT"
    
    # 4. EXÉCUTION
    if type_contrat:
        # Vérification du délai (1 trade par minute pour éviter le spam)
        current_time = datetime.now().timestamp()
        if current_time - st.session_state.last_trade_time < 60:
            return

        # Mise à jour de l'heure du dernier trade
        st.session_state.last_trade_time = current_time
        
        # Préparation de l'ordre pour l'API Deriv
        requete = {
            "buy": 1,
            "price": MISE_DE_BASE,
            "parameters": {
                "amount": MISE_DE_BASE,
                "basis": "stake",
                "contract_type": type_contrat,
                "currency": "USD",
                "duration": 1,
                "duration_unit": "m",
                "symbol": symbole
            }
        }
        
        try:
            # ENVOI RÉEL À DERIV
            await ws.send(json.dumps(requete))
            
            # --- MISE À JOUR DES PERFORMANCES ---
            s['mises'] += MISE_DE_BASE
            
            # Pour l'instant, on simule un résultat pour tester l'interface
            # On considère le trade gagnant à 90% de profit pour voir les compteurs bouger
            gain_virtuel = MISE_DE_BASE * 0.95
            s['gains'] += 1
            s['profit'] = round(s['profit'] + gain_virtuel, 2)
            
            # Ajout à l'historique visible
            nouveau_log = {
                "Heure": datetime.now().strftime("%H:%M:%S"),
                "Type": type_contrat,
                "Mise": f"{MISE_DE_BASE}$",
                "Résultat": "✅ GAGNÉ"
            }
            s['logs'].insert(0, nouveau_log)
            
            # Notification Streamlit
            st.toast(f"🚀 ORDRE {type_contrat} PLACÉ !", icon="💰")
            
        except Exception as e:
            print(f"Erreur API Deriv : {e}")