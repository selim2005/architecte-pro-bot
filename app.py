import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import asyncio
from bot_test import executer_ordre_automatique

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Kasaa Trade - Architecte Pro", layout="wide")

# --- INITIALISATION DE L'ÉTAT (SESSION STATE) ---
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'profit': 0.0,
        'victoires': 0,
        'pertes': 0,
        'martingale': 0,
        'logs': []
    }

if 'historique_prix' not in st.session_state:
    st.session_state.historique_prix = pd.DataFrame(columns=['Heure', 'Prix'])

# --- INTERFACE UTILISATEUR ---
st.title("🚀 Kasaa Trade - Bot Architecte Pro")
st.sidebar.header("Configuration")

jeton_utilisateur = st.sidebar.text_input("Jeton Deriv API", type="password")
marche_selectionne = st.sidebar.selectbox("Marché", ["R_10", "R_25", "R_50", "R_100"])

col1, col2, col3 = st.columns(3)
col1.metric("Profit Total", f"{st.session_state.stats['profit']:.2f} $")
col2.metric("Victoires", st.session_state.stats['victoires'])
col3.metric("Pertes", st.session_state.stats['pertes'])

# --- ZONE DU GRAPHIQUE ---
st.subheader("Analyse en Temps Réel")
placeholder_graph = st.empty()

async def demarrer_moteur_kasaa(token, symbole):
    while True:
        # Simulation de prix pour l'exemple (à remplacer par ton flux WebSocket)
        nouveau_prix = 1250.0 + (datetime.now().second % 10) 
        nouvelle_ligne = {'Heure': datetime.now().strftime("%H:%M:%S"), 'Prix': nouveau_prix}
        
        # Mise à jour du DataFrame
        st.session_state.historique_prix = pd.concat([
            st.session_state.historique_prix, 
            pd.DataFrame([nouvelle_ligne])
        ]).tail(20)

        # Création du graphique Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=st.session_state.historique_prix['Heure'], 
            y=st.session_state.historique_prix['Prix'],
            mode='lines+markers',
            name='Prix Actuel'
        ))
        
        # Correction de l'erreur DuplicateElementKey avec une clé unique
        placeholder_graph.plotly_chart(fig, use_container_width=True, key="graphique_principal_kasaa")

        # Appel de la logique de trading (bot_test.py)
        # On passe un DataFrame factice 'df' pour le calcul du RSI
        df_simule = st.session_state.historique_prix.rename(columns={'Prix': 'close'})
        await executer_ordre_automatique(None, symbole, "ANALYSE...", df_simule)

        await asyncio.sleep(2)

# --- BOUTONS DE CONTRÔLE ---
if st.sidebar.button("Lancer le Bot"):
    if jeton_utilisateur:
        st.success("Bot démarré !")
        asyncio.run(demarrer_moteur_kasaa(jeton_utilisateur, marche_selectionne))
    else:
        st.error("Veuillez entrer un jeton API.")

# --- LOGS DE TRADING ---
st.subheader("Journal d'activités (Logs)")
if st.session_state.stats['logs']:
    df_logs = pd.DataFrame(st.session_state.stats['logs'])
    st.table(df_logs)