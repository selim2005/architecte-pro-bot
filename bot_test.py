import pandas as pd
import pandas_ta as ta
import streamlit as st

# ═══════════════════════════════════════════
#        PARAMÈTRES GLOBAUX DE SÉCURITÉ
# ═══════════════════════════════════════════
MISE_DE_BASE = 10.0
LIMIT_STOP_LOSS = -30.0       # Arrêt si perte globale dépasse 30$
LIMIT_TAKE_PROFIT = 100.0     # Arrêt si gain global atteint 100$
MARTINGALE_MAX = 3            # Maximum 3 niveaux de Martingale (10→20→40)
RATIO_RISQUE_REWARD = 2.0     # On vise toujours 2x la mise en gain

# ═══════════════════════════════════════════
#        ANALYSE TECHNIQUE MULTI-INDICATEURS
# ═══════════════════════════════════════════
def analyser_marche(df: pd.DataFrame) -> dict:
    """
    Analyse le marché avec 3 indicateurs croisés.
    Retourne un signal seulement si TOUS les indicateurs sont alignés.
    Principe : Observer → Confirmer → Décider
    """
    if len(df) < 30:
        return {"signal": None, "raison": "Données insuffisantes"}

    # --- Indicateur 1 : RSI (14 périodes) ---
    df['rsi'] = ta.rsi(df['close'], length=14)

    # --- Indicateur 2 : EMA (Tendance) ---
    df['ema_rapide'] = ta.ema(df['close'], length=9)
    df['ema_lente']  = ta.ema(df['close'], length=21)

    # --- Indicateur 3 : MACD (Momentum) ---
    macd_data        = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['macd']       = macd_data['MACD_12_26_9']
    df['macd_signal']= macd_data['MACDs_12_26_9']

    # Récupération des dernières valeurs
    rsi         = df['rsi'].iloc[-1]
    ema_rapide  = df['ema_rapide'].iloc[-1]
    ema_lente   = df['ema_lente'].iloc[-1]
    macd        = df['macd'].iloc[-1]
    macd_sig    = df['macd_signal'].iloc[-1]

    # ══════════════════════════════════════
    #  SIGNAL ACHAT — 3 conditions requises
    # ══════════════════════════════════════
    signal_achat = (
        rsi < 35 and                    # RSI : zone de survente
        ema_rapide > ema_lente and      # EMA : tendance haussière
        macd > macd_sig                 # MACD : momentum positif
    )

    # ══════════════════════════════════════
    #  SIGNAL VENTE — 3 conditions requises
    # ══════════════════════════════════════
    signal_vente = (
        rsi > 65 and                    # RSI : zone de surachat
        ema_rapide < ema_lente and      # EMA : tendance baissière
        macd < macd_sig                 # MACD : momentum négatif
    )

    if signal_achat:
        return {
            "signal": "ACHAT (CALL)",
            "rsi": round(rsi, 2),
            "raison": f"RSI={round(rsi,1)} | EMA haussière | MACD positif"
        }
    elif signal_vente:
        return {
            "signal": "VENTE (PUT)",
            "rsi": round(rsi, 2),
            "raison": f"RSI={round(rsi,1)} | EMA baissière | MACD négatif"
        }
    else:
        return {"signal": None, "raison": "Pas de signal confirmé — On attend."}


# ═══════════════════════════════════════════
#        EXÉCUTION DE L'ORDRE
# ═══════════════════════════════════════════
async def executer_ordre_automatique(ws, symbole: str, df: pd.DataFrame):
    """
    Exécute un ordre uniquement si le marché est confirmé.
    Principe : Pas d'action sans certitude.
    """
    s = st.session_state.stats

    # --- Vérification des limites globales ---
    if s['profit'] <= LIMIT_STOP_LOSS:
        st.error("🛑 STOP LOSS GLOBAL ATTEINT. Capital protégé. Session arrêtée.")
        return

    if s['profit'] >= LIMIT_TAKE_PROFIT:
        st.success("🎯 OBJECTIF ATTEINT ! Excellent travail. Session terminée.")
        return

    # --- Vérification du plafond Martingale ---
    if s['martingale'] >= MARTINGALE_MAX:
        st.warning("⚠️ Plafond Martingale atteint. Pause obligatoire. Réinitialisation.")
        s['martingale'] = 0
        return

    # --- Analyse du marché ---
    analyse = analyser_marche(df)

    if not analyse["signal"]:
        # Pas de signal → on n'agit pas → on attend
        st.info(f"⏳ {analyse['raison']} — Le bot patiente.")
        return

    decision = analyse["signal"]

    # --- Calcul de la mise avec plafond de sécurité ---
    mise_actuelle = min(
        MISE_DE_BASE * (2 ** s['martingale']),
        MISE_DE_BASE * (2 ** MARTINGALE_MAX)  # Plafond absolu
    )

    # --- Envoi de l'ordre via WebSocket Deriv ---
    # ⚡ Ici tu connectes ton API Deriv pour l'ordre réel
    # await ws.send(json.dumps({...}))  ← à implémenter

    # --- Enregistrement dans le journal ---
    s['logs'].insert(0, {
        "Heure"        : pd.Timestamp.now().strftime("%H:%M:%S"),
        "Marché"       : symbole,
        "Signal RSI"   : analyse['rsi'],
        "Raison"       : analyse['raison'],
        "Type d'Ordre" : decision,
        "Mise ($)"     : round(mise_actuelle, 2),
        "Statut"       : "⏳ En cours..."
    })

    st.info(f"📤 Ordre envoyé : {decision} | Mise : {mise_actuelle}$ | {analyse['raison']}")