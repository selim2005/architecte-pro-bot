import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="KASAA TRADE PROFESSIONNEL", layout="wide")

# --- DESIGN ET STYLE VISUEL ---
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(125deg, #000000, #050505, #001a1a); 
        color: white; 
    }
    .carte-statistique { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #444444; 
        text-align: center; 
    }
    .titre-statistique { color: #8B949E; font-size: 12px; text-transform: uppercase; font-weight: bold; }
    .valeur-statistique { font-size: 22px; font-weight: bold; margin-top: 5px; }
    .boite-signal { 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center; 
        font-weight: bold; 
        font-size: 18px;
        margin-bottom: 20px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES DONNÉES ---
if 'statistiques' not in st.session_state:
    st.session_state.statistiques = {
        'nombre_gains': 0, 
        'nombre_pertes': 0, 
        'total_encaisse': 0.0, 
        'total_perdu': 0.0, 
        'historique_complet': []
    }
if 'bougies' not in st.session_state:
    st.session_state.bougies = []

# --- INTERFACE UTILISATEUR ---
zone_information = st.empty()
zone_signal = st.empty()
zone_graphique = st.empty()

colonne1, colonne2, colonne3, colonne4 = st.columns(4)
affichage_gains = colonne1.empty()
affichage_pertes = colonne2.empty()
affichage_somme_gagne = colonne3.empty()
affichage_somme_perdue = colonne4.empty()

st.markdown("---")
zone_historique = st.empty()

# --- 1. FONCTION D'EXÉCUTION DES TRADES ---
async def envoyer_ordre_achat(websocket, type_contrat, symbole_marche, montant_mise):
    # Envoi de la commande d'achat réelle à Deriv
    commande = {
        "buy": 1,
        "price": montant_mise,
        "parameters": {
            "amount": montant_mise,
            "basis": "stake",
            "contract_type": type_contrat, # CALL pour hausse, PUT pour baisse
            "currency": "USD",
            "duration": 1,
            "duration_unit": "m", # Durée de 1 minute
            "symbol": symbole_marche
        }
    }
    await websocket.send(json.dumps(commande))

# --- 2. STRATÉGIE DE CROISEMENT DE MOYENNES MOBILES ---
def analyser_strategie(donnees_dataframe):
    # Calcul des moyennes mobiles pour détecter la tendance
    # Moyenne rapide (5 dernières bougies) et lente (10 dernières bougies)
    moyenne_rapide = donnees_dataframe['close'].rolling(window=5).mean().iloc[-1]
    moyenne_lente = donnees_dataframe['close'].rolling(window=10).mean().iloc[-1]
    
    if moyenne_rapide > moyenne_lente:
        return "CALL", "🟢 SIGNAL DE HAUSSE DÉTECTÉ"
    elif moyenne_rapide < moyenne_lente:
        return "PUT", "🔴 SIGNAL DE BAISSE DÉTECTÉ"
    else:
        return None, "⚪ ANALYSE EN COURS..."

# --- 3. MOTEUR DE CONNEXION ET TRADING ---
async def demarrer_moteur_kasaa(jeton_api, code_marche):
    adresse_serveur = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(adresse_serveur) as websocket:
        # Authentification officielle
        await websocket.send(json.dumps({"authorize": jeton_api}))
        reponse_auth = json.loads(await websocket.recv())
        
        if "error" in reponse_auth:
            st.error("Erreur de connexion : Jeton invalide"); return
        
        nom_utilisateur = reponse_auth['authorize']['fullname']
        solde_actuel = reponse_auth['authorize']['balance']
        zone_information.success(f"Utilisateur : {nom_utilisateur} | Solde disponible : {solde_actuel} USD")

        # Souscription au flux de données
        await websocket.send(json.dumps({
            "ticks_history": code_marche, 
            "subscribe": 1, 
            "end": "latest",
            "count": 50, 
            "style": "candles", 
            "granularity": 60
        }))

        while True:
            message_recu = json.loads(await websocket.recv())
            
            if "ohlc" in message_recu:
                donnees = message_recu['ohlc']
                nouvelle_bougie = {
                    'time': datetime.fromtimestamp(int(donnees['open_time'])), 
                    'open': float(donnees['open']), 
                    'high': float(donnees['high']), 
                    'low': float(donnees['low']), 
                    'close': float(donnees['close'])
                }
                
                # Mise à jour des bougies stockées
                if st.session_state.bougies and st.session_state.bougies[-1]['time'] == nouvelle_bougie['time']:
                    st.session_state.bougies[-1] = nouvelle_bougie
                else:
                    st.session_state.bougies.append(nouvelle_bougie)
                    if len(st.session_state.bougies) > 50: st.session_state.bougies.pop(0)
                    
                    # Exécution de la stratégie à chaque nouvelle bougie
                    if len(st.session_state.bougies) >= 10:
                        df = pd.DataFrame(st.session_state.bougies)
                        decision_trade, texte_signal = analyser_strategie(df)
                        
                        zone_signal.markdown(f'<div class="boite-signal" style="border: 2px solid {"#00ffbb" if "HAUSSE" in texte_signal else "#ff3333" if "BAISSE" in texte_signal else "#777"}">{texte_signal}</div>', unsafe_allow_html=True)
                        
                        if decision_trade:
                            await envoyer_ordre_achat(websocket, decision_trade, code_marche, 10.0)

                # MISE À JOUR DE L'INTERFACE
                stats = st.session_state.statistiques
                affichage_gains.markdown(f'<div class="carte-statistique"><p class="titre-statistique">Nombre de Gains</p><p class="valeur-statistique" style="color:#00ffbb">{stats["nombre_gains"]}</p></div>', unsafe_allow_html=True)
                affichage_pertes.markdown(f'<div class="carte-statistique"><p class="titre-statistique">Nombre de Pertes</p><p class="valeur-statistique" style="color:#ff3333">{stats["nombre_pertes"]}</p></div>', unsafe_allow_html=True)
                affichage_somme_gagne.markdown(f'<div class="carte-statistique"><p class="titre-statistique">Somme Encaissée</p><p class="valeur-statistique">+{stats["total_encaisse"]:.2f} $</p></div>', unsafe_allow_html=True)
                affichage_somme_perdue.markdown(f'<div class="carte-statistique"><p class="titre-statistique">Somme Perdue</p><p class="valeur-statistique">-{stats["total_perdu"]:.2f} $</p></div>', unsafe_allow_html=True)

                figure_graphique = go.Figure(data=[go.Candlestick(x=pd.DataFrame(st.session_state.bougies)['time'], open=pd.DataFrame(st.session_state.bougies)['open'], high=pd.DataFrame(st.session_state.bougies)['high'], low=pd.DataFrame(st.session_state.bougies)['low'], close=pd.DataFrame(st.session_state.bougies)['close'])])
                figure_graphique.update_layout(template="plotly_dark", height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                zone_graphique.plotly_chart(figure_graphique, use_container_width=True, key=f"graphique_{code_marche}")

            await asyncio.sleep(0.5)

# --- PANNEAU DE CONFIGURATION ---
with st.sidebar:
    st.header("CONFIGURATION KASAA")
    jeton_utilisateur = st.text_input("VOTRE JETON API DERIV", type="password")
    marche_selectionne = st.selectbox("CHOISIR LE MARCHÉ", [
        "R_10", "R_25", "R_50", "R_75", "R_100", 
        "1HZ10V", "1HZ50V", "1HZ100V", 
        "B_300", "B_500", "B_1000", 
        "C_300", "C_500", "C_1000"
    ])
    bouton_activation = st.button("DÉMARRER LE TRADING RÉEL")

if bouton_activation and jeton_utilisateur:
    asyncio.run(demarrer_moteur_kasaa(jeton_utilisateur, marche_selectionne))