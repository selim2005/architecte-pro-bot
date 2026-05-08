import streamlit as st
from datetime import datetime

async def executer_ordre_automatique(ws, symbole, status, df):
    # Initialisation locale si besoin
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'mises': 0, 'gains': 0, 'pertes': 0, 'profit': 0.0, 
            'somme_gains': 0.0, 'somme_pertes': 0.0, 'logs': []
        }
    
    s = st.session_state.stats
    
    # 1. PARAMÈTRES DE BASE
    MISE_INITIALE = 10.0
    MAX_MARTINGALE = 5
    
    # 2. VÉRIFICATION DU SIGNAL
    # On ne trade que si on a un signal clair (Hausse ou Baisse)
    type_contrat = ""
    if "HAUSSIER" in status:
        type_contrat = "CALL"
    elif "VENDEUSE" in status:
        type_contrat = "PUT"
    else:
        return # On arrête ici si c'est "Indécision"

    # 3. CALCUL DE LA MISE ACTUELLE (MARTINGALE)
    # Si on a des pertes, on multiplie la mise
    niveau_martingale = s['pertes'] if s['pertes'] < MAX_MARTINGALE else 0
    mise_actuelle = MISE_INITIALE * (2 ** niveau_martingale)

    # 4. SIMULATION DE L'EXÉCUTION (Pour le test)
    # Ici, on simule si le trade est gagnant ou perdant par rapport à la bougie
    last_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    
    res_txt = ""
    profit_operation = 0.0
    
    # Logique de victoire simplifiée pour le test
    # (En réel, c'est le résultat de l'API Deriv qui remplace ça)
    if (type_contrat == "CALL" and last_close > prev_close) or \
       (type_contrat == "PUT" and last_close < prev_close):
        res_txt = "X GAGNÉ"
        profit_operation = mise_actuelle * 0.95 # Gain de 95%
        s['gains'] += 1
        s['somme_gains'] += profit_operation
        s['profit'] += profit_operation
        # Reset de la martingale après un gain
        # s['pertes'] = 0 (Optionnel : pour revenir à la mise de base)
    else:
        res_txt = "X PERDU"
        profit_operation = -mise_actuelle
        s['pertes'] += 1
        s['somme_pertes'] += abs(profit_operation)
        s['profit'] += profit_operation

    # 5. ENREGISTREMENT DANS L'HISTORIQUE
    nouveau_log = {
        "Heure": datetime.now().strftime("%H:%M:%S"),
        "Marché": symbole,
        "Type": type_contrat,
        "Mise": f"{mise_actuelle:.2f} $",
        "Résultat": res_txt,
        "Profit Net": f"{profit_operation:.2f} $"
    }
    
    # On ajoute au début de la liste pour voir le dernier trade en haut
    s['logs'].insert(0, nouveau_log)
    s['mises'] += 1

    # Petit message de succès sur l'interface
    if res_txt == "X GAGNÉ":
        st.toast(f"Victoire ! +{profit_operation:.2f}$", icon="💰")
    else:
        st.toast(f"Perte... {profit_operation:.2f}$", icon="📉")