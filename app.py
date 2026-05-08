import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import asyncio
import websockets
import json
import time

# ═══════════════════════════════════════════
#        CONFIGURATION DE LA PAGE
# ═══════════════════════════════════════════
st.set_page_config(
    page_title="KASAA TRADE - SYSTÈME PRO",
    layout="wide",
    page_icon="💎"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1c212d;
        border: 1px solid #00ff88;
        border-radius: 10px;
        padding: 15px;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
#        INITIALISATION DE LA SESSION
# ═══════════════════════════════════════════
def init_session():
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'profit'     : 0.0,
            'victoires'  : 0,
            'pertes'     : 0,
            'martingale' : 0,
            'logs'       : []
        }
    if 'bot_actif' not in st.session_state:
        st.session_state.bot_actif = False
    if 'prix_historique' not in st.session_state:
        st.session_state.prix_historique = []

init_session()
s = st.session_state.stats


# ═══════════════════════════════════════════
#        CONNEXION DERIV — DONNÉES RÉELLES
# ═══════════════════════════════════════════
MARCHE_SYMBOLES = {
    "Volatility 10 Index"     : "R_10",
    "Volatility 25 Index"     : "R_25",
    "Volatility 50 Index"     : "R_50",
    "Volatility 75 Index"     : "R_75",
    "Volatility 100 Index"    : "R_100",
    "Volatility 10 (1s) Index": "1HZ10V",
    "Volatility 25 (1s) Index": "1HZ25V"
}

async def recuperer_ticks_deriv(symbole_api: str, n_ticks: int = 50) -> list:
    """
    Récupère les vrais prix du marché via l'API Deriv WebSocket.
    """
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(url) as ws:
            requete = {
                "ticks_history": symbole_api,
                "count"        : n_ticks,
                "end"          : "latest",
                "style"        : "ticks"
            }
            await ws.send(json.dumps(requete))
            reponse = json.loads(await ws.recv())

            if "history" in reponse:
                prix = reponse["history"]["prices"]
                return [float(p) for p in prix]
            else:
                st.warning("⚠️ Erreur API Deriv : " + str(reponse.get("error", {}).get("message", "")))
                return []
    except Exception as e:
        st.error(f"❌ Connexion Deriv échouée : {e}")
        return []


# ═══════════════════════════════════════════
#        INTERFACE — TITRE ET MÉTRIQUES
# ═══════════════════════════════════════════
st.title("💎 KASAA TRADE — L'Architecte Pro")

# Calcul du taux de victoire
total_trades = s['victoires'] + s['pertes']
taux_victoire = (s['victoires'] / total_trades * 100) if total_trades > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 PROFIT TOTAL",     f"{s['profit']:.2f} $")
col2.metric("✅ VICTOIRES",         s['victoires'])
col3.metric("📈 TAUX DE VICTOIRE",  f"{taux_victoire:.1f} %")
col4.metric("🎲 NIVEAU MARTINGALE", s['martingale'])

# Alerte Martingale élevée
if s['martingale'] >= 2:
    st.warning(f"⚠️ Martingale niveau {s['martingale']} — Prudence. Prochaine mise : {10 * (2 ** s['martingale'])}$")


# ═══════════════════════════════════════════
#        GRAPHIQUE EN TEMPS RÉEL
# ═══════════════════════════════════════════
st.subheader("📊 Analyse du Marché en Temps Réel")
placeholder_graphe   = st.empty()
placeholder_signal   = st.empty()
placeholder_statut   = st.empty()


# ═══════════════════════════════════════════
#        SIDEBAR — PARAMÈTRES
# ═══════════════════════════════════════════
st.sidebar.header("⚙️ PARAMÈTRES DE PRODUCTION")
jeton_api = st.sidebar.text_input("🔑 Jeton API Deriv", type="password")

liste_marches = list(MARCHE_SYMBOLES.keys())
marche = st.sidebar.selectbox("📌 Sélectionnez le Marché", liste_marches)
symbole_api = MARCHE_SYMBOLES[marche]

intervalle = st.sidebar.slider("⏱️ Intervalle d'analyse (secondes)", 3, 30, 5)

st.sidebar.markdown("---")

# --- Boutons Démarrer / Arrêter ---
col_btn1, col_btn2 = st.sidebar.columns(2)

if col_btn1.button("▶️ DÉMARRER", use_container_width=True):
    if not jeton_api:
        st.sidebar.error("🔑 Jeton API requis.")
    else:
        st.session_state.bot_actif = True

if col_btn2.button("⏹️ ARRÊTER", use_container_width=True):
    st.session_state.bot_actif = False
    st.sidebar.info("Bot arrêté proprement.")


# ═══════════════════════════════════════════
#        MOTEUR DU BOT — CYCLE UNIQUE
# ═══════════════════════════════════════════
async def cycle_trading():
    """
    Un seul cycle d'analyse et de décision.
    Streamlit recharge la page à chaque cycle via st.rerun().
    """
    from bot_test import analyser_marche, executer_ordre_automatique

    # 1. Récupération des vraies données
    prix = await recuperer_ticks_deriv(symbole_api, n_ticks=50)

    if len(prix) < 30:
        placeholder_statut.warning("⏳ Données insuffisantes — Attente du marché...")
        return

    df = pd.DataFrame({'close': prix})

    # 2. Mise à jour de l'historique de prix pour le graphique
    st.session_state.prix_historique = prix

    # 3. Affichage du graphique avec vraies données
    fig = go.Figure(go.Scatter(
        y=prix,
        mode='lines',
        line=dict(color='#00ff88', width=2),
        name=marche
    ))
    fig.update_layout(
        template="plotly_dark",
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        title=dict(text=f"📈 {marche}", font=dict(color='#00ff88'))
    )
    placeholder_graphe.plotly_chart(fig, use_container_width=True)

    # 4. Analyse et décision
    analyse = analyser_marche(df)
    if analyse["signal"]:
        placeholder_signal.success(f"🎯 Signal détecté : **{analyse['signal']}** — {analyse['raison']}")
    else:
        placeholder_signal.info(f"⏳ {analyse['raison']}")

    # 5. Exécution de l'ordre
    await executer_ordre_automatique(None, marche, df)


# ═══════════════════════════════════════════
#        BOUCLE PRINCIPALE STREAMLIT
# ═══════════════════════════════════════════
if st.session_state.bot_actif:
    placeholder_statut.success(f"🟢 Bot actif sur **{marche}** — Analyse toutes les {intervalle}s")
    asyncio.run(cycle_trading())
    time.sleep(intervalle)
    st.rerun()  # Streamlit recharge la page proprement
else:
    placeholder_statut.info("🔵 Bot en veille. Appuyez sur DÉMARRER.")


# ═══════════════════════════════════════════
#        JOURNAL DE TRADING
# ═══════════════════════════════════════════
st.subheader("📜 Journal de Trading")
if s['logs']:
    df_logs = pd.DataFrame(s['logs'])
    st.dataframe(df_logs, use_container_width=True)
else:
    st.info("Aucun trade enregistré pour cette session.")