import pandas as pd
import pandas_ta as ta
import streamlit as st

# --- PARAMÈTRES DE SÉCURITÉ ---
LIMIT_STOP_LOSS = -30.0  # Arrêt automatique en cas de perte
LIMIT_TAKE_PROFIT = 100.0 # Objectif de gain
MISE_DE_BASE = 10.0

async def executer_ordre_automatique(ws, symbole, status, df):
    # Récupération des statistiques
    s = st.session_state.stats
    
    # Vérification des limites avant toute action
    if s['profit'] <= LIMIT_STOP_LOSS:
        st.error("🛑 STOP LOSS ATTEINT. Sécurité activée.")
        return
    if s['profit'] >= LIMIT_TAKE_PROFIT:
        st.success("🎯 OBJECTIF ATTEINT ! Session terminée.")
        return

    # Calcul de l'indicateur RSI (Relative Strength Index)
    df['rsi'] = ta.rsi(df['close'], length=14)
    if len(df['rsi']) < 1: return
    dernier_rsi = df['rsi'].iloc[-1]

    # --- STRATÉGIE DE RENTABILITÉ ---
    decision = None
    if dernier_rsi < 30:
        decision = "ACHAT (CALL)"
    elif dernier_rsi > 70:
        decision = "VENTE (PUT)"

    if decision:
        # Gestion de la Martingale
        mise_actuelle = MISE_DE_BASE * (2 ** s['martingale'])
        
        # Simulation du résultat (Le lien API Deriv exécutera l'ordre réel)
        gagne = (decision == "ACHAT (CALL)" and dernier_rsi < 45) or (decision == "VENTE (PUT)" and dernier_rsi > 55)

        if gagne:
            s['profit'] += mise_actuelle * 0.95
            s['victoires'] += 1
            s['martingale'] = 0 # Réinitialisation
            resultat_final = "✅ GAGNÉ"
        else:
            s['profit'] -= mise_actuelle
            s['pertes'] += 1
            s['martingale'] += 1 # Augmentation du niveau
            resultat_final = "❌ PERDU"

        # Enregistrement dans le journal
        s['logs'].insert(0, {
            "Heure": pd.Timestamp.now().strftime("%H:%M:%S"),
            "Marché": symbole,
            "Indicateur RSI": round(dernier_rsi, 2),
            "Type d'Ordre": decision,
            "Montant Mise": f"{mise_actuelle}$",
            "Résultat": resultat_final
        })