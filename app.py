# ═══════════════════════════════════════════════════════════════
#   KASAA TRADE — Interface Premium | Fond Spatial Animé
# ═══════════════════════════════════════════════════════════════

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from bot_logic import (
    analyser_marche, executer_cycle, recuperer_ticks,
    MARCHE_SYMBOLES, STOP_LOSS, TAKE_PROFIT, MARTINGALE_MAX, MISE_DE_BASE
)

# ───────────────────────────────────────────
#  CONFIGURATION
# ───────────────────────────────────────────
st.set_page_config(
    page_title="KASAA TRADE — PRO",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="expanded"
)

# ───────────────────────────────────────────
#  FOND SPATIAL ANIMÉ (Étoiles + Comètes)
# ───────────────────────────────────────────
st.markdown("""
<style>
/* Fond noir profond */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #000010 !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
    background: rgba(5, 5, 25, 0.92) !important;
    border-right: 1px solid #1a2a5e;
}
.block-container { padding-top: 1rem; }

/* Canvas de fond fixé */
#space-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
}

/* Contenu au-dessus du canvas */
[data-testid="stAppViewContainer"] > div { position: relative; z-index: 1; }

/* Métriques stylisées */
div[data-testid="stMetric"] {
    background: rgba(15, 20, 50, 0.85) !important;
    border: 1px solid #00ff88;
    border-radius: 12px;
    padding: 16px;
    backdrop-filter: blur(8px);
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.15);
}
div[data-testid="stMetricLabel"] > div {
    color: #a0aec0 !important;
    font-weight: 600;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
}
div[data-testid="stMetricValue"] > div {
    color: #f5f5f5 !important;
    font-weight: 700;
    text-shadow: 0 0 10px rgba(0,255,136,0.3);
}

/* Titre principal */
h1 {
    color: #f5f5f5 !important;
    text-shadow: 0 0 20px rgba(0, 200, 255, 0.5), 0 0 40px rgba(0, 100, 255, 0.3);
    font-weight: 800 !important;
    letter-spacing: 0.03em;
}
h2, h3 {
    color: #c0d0ff !important;
    font-weight: 700 !important;
}

/* Boutons */
.stButton > button {
    background: linear-gradient(135deg, #0066ff, #00ccff) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em;
    transition: all 0.2s;
    box-shadow: 0 0 15px rgba(0, 150, 255, 0.4);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 25px rgba(0, 200, 255, 0.6) !important;
}

/* Selectbox et inputs */
.stSelectbox > div > div, .stTextInput > div > div {
    background: rgba(10, 15, 40, 0.9) !important;
    border: 1px solid #1a3a6e !important;
    color: #f5f5f5 !important;
    border-radius: 8px !important;
}

/* Tableau journal */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* Slider */
.stSlider > div { color: #a0aec0 !important; }

/* Texte général */
p, label, .stMarkdown { color: #c0cce0 !important; }
</style>

<canvas id="space-canvas"></canvas>

<script>
(function() {
    const canvas = document.getElementById('space-canvas');
    const ctx    = canvas.getContext('2d');
    let W, H, stars = [], particles = [], comets = [];

    function resize() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    // ── Étoiles fixes scintillantes ──
    function creerEtoiles(n) {
        stars = [];
        for (let i = 0; i < n; i++) {
            stars.push({
                x       : Math.random() * W,
                y       : Math.random() * H,
                r       : Math.random() * 1.4 + 0.2,
                alpha   : Math.random(),
                vitesse : 0.003 + Math.random() * 0.012,
                phase   : Math.random() * Math.PI * 2,
                couleur : ['#ffffff','#aaddff','#ffeedd','#ddccff'][Math.floor(Math.random()*4)]
            });
        }
    }
    creerEtoiles(250);

    // ── Particules multicolores flottantes ──
    const COULEURS = ['#ff4488','#44ffaa','#4488ff','#ffaa00','#aa44ff','#00ffff','#ff6600'];
    function creerParticules(n) {
        particles = [];
        for (let i = 0; i < n; i++) {
            particles.push({
                x   : Math.random() * W,
                y   : Math.random() * H,
                r   : Math.random() * 2.5 + 0.5,
                vx  : (Math.random() - 0.5) * 0.3,
                vy  : (Math.random() - 0.5) * 0.3,
                alpha: 0.15 + Math.random() * 0.25,
                c   : COULEURS[Math.floor(Math.random() * COULEURS.length)]
            });
        }
    }
    creerParticules(80);

    // ── Comètes / étoiles filantes ──
    function lancerComete() {
        const bord = Math.random() < 0.5;
        comets.push({
            x     : bord ? 0 : Math.random() * W,
            y     : bord ? Math.random() * H * 0.5 : 0,
            vx    : 4 + Math.random() * 6,
            vy    : 2 + Math.random() * 4,
            len   : 80 + Math.random() * 120,
            alpha : 0.9,
            c     : COULEURS[Math.floor(Math.random() * COULEURS.length)],
            width : 1.5 + Math.random() * 1.5
        });
    }

    // Lancer une comète toutes les 2.5–5 secondes
    setInterval(lancerComete, 2500 + Math.random() * 2500);
    lancerComete();

    // ── Boucle de rendu ──
    let frame = 0;
    function draw() {
        ctx.clearRect(0, 0, W, H);

        // Fond dégradé
        const grad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, Math.max(W,H)*0.75);
        grad.addColorStop(0, 'rgba(5,5,30,1)');
        grad.addColorStop(1, 'rgba(0,0,10,1)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, W, H);

        frame++;

        // Étoiles scintillantes
        stars.forEach(s => {
            s.alpha = 0.4 + 0.6 * Math.abs(Math.sin(frame * s.vitesse + s.phase));
            ctx.globalAlpha = s.alpha;
            ctx.fillStyle   = s.couleur;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
            ctx.fill();
            // Lueur sur les grosses étoiles
            if (s.r > 1.0) {
                ctx.globalAlpha = s.alpha * 0.3;
                ctx.beginPath();
                ctx.arc(s.x, s.y, s.r * 3, 0, Math.PI * 2);
                ctx.fill();
            }
        });

        // Particules multicolores
        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
            if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
            ctx.globalAlpha = p.alpha;
            ctx.fillStyle   = p.c;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
        });

        // Comètes
        comets = comets.filter(c => c.alpha > 0.02);
        comets.forEach(c => {
            ctx.globalAlpha = c.alpha;
            const grad2 = ctx.createLinearGradient(c.x, c.y, c.x - c.len, c.y - c.len * 0.5);
            grad2.addColorStop(0, c.c);
            grad2.addColorStop(1, 'transparent');
            ctx.strokeStyle = grad2;
            ctx.lineWidth   = c.width;
            ctx.lineCap     = 'round';
            ctx.beginPath();
            ctx.moveTo(c.x, c.y);
            ctx.lineTo(c.x - c.len, c.y - c.len * 0.5);
            ctx.stroke();
            c.x     += c.vx;
            c.y     += c.vy;
            c.alpha -= 0.012;
        });

        ctx.globalAlpha = 1;
        requestAnimationFrame(draw);
    }
    draw();
})();
</script>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────
#  SESSION STATE
# ───────────────────────────────────────────
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'profit': 0.0, 'victoires': 0,
        'pertes': 0, 'martingale': 0, 'logs': []
    }
if 'bot_actif'   not in st.session_state: st.session_state.bot_actif   = False
if 'last_action' not in st.session_state: st.session_state.last_action = "En attente..."
if 'prix_data'   not in st.session_state: st.session_state.prix_data   = []

s = st.session_state.stats


# ───────────────────────────────────────────
#  TITRE
# ───────────────────────────────────────────
st.markdown("# 💎 KASAA TRADE — L'Architecte Pro")
st.markdown("---")


# ───────────────────────────────────────────
#  MÉTRIQUES
# ───────────────────────────────────────────
total  = s['victoires'] + s['pertes']
taux   = round(s['victoires'] / total * 100, 1) if total > 0 else 0.0
profit_color = "🟢" if s['profit'] >= 0 else "🔴"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Profit Total",      f"{s['profit']:.2f} $",  delta=f"{profit_color}")
c2.metric("✅ Victoires",          s['victoires'])
c3.metric("❌ Pertes",             s['pertes'])
c4.metric("📈 Taux de Victoire",   f"{taux} %")
c5.metric("🎲 Martingale",         f"Niv. {s['martingale']}")

# Alerte dynamique
if s['martingale'] >= 2:
    prochaine_mise = MISE_DE_BASE * (2 ** s['martingale'])
    st.warning(f"⚠️ Martingale Niveau {s['martingale']} — Prochaine mise : **{prochaine_mise:.0f}$** — Restez calme.")
if s['profit'] <= STOP_LOSS:
    st.error("🛑 STOP LOSS GLOBAL ATTEINT — Session protégée.")
if s['profit'] >= TAKE_PROFIT:
    st.success("🎯 OBJECTIF ATTEINT — Excellente session !")


# ───────────────────────────────────────────
#  GRAPHIQUE
# ───────────────────────────────────────────
st.subheader("📊 Analyse du Marché en Temps Réel")
ph_graphe  = st.empty()
ph_analyse = st.empty()
ph_statut  = st.empty()

def afficher_graphe(prix: list, marche: str):
    if not prix:
        ph_graphe.info("En attente de données marché...")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=prix, mode='lines',
        line=dict(color='#00ff88', width=2),
        fill='tozeroy',
        fillcolor='rgba(0,255,136,0.05)',
        name=marche
    ))
    fig.update_layout(
        template   ="plotly_dark",
        height     = 320,
        paper_bgcolor="rgba(5,5,25,0.0)",
        plot_bgcolor ="rgba(5,5,25,0.6)",
        margin     = dict(l=20, r=20, t=30, b=20),
        title      = dict(text=f"📈 {marche}", font=dict(color='#00ff88', size=14)),
        xaxis      = dict(showgrid=False),
        yaxis      = dict(gridcolor='rgba(255,255,255,0.05)')
    )
    ph_graphe.plotly_chart(fig, use_container_width=True)


# ───────────────────────────────────────────
#  SIDEBAR
# ───────────────────────────────────────────
st.sidebar.markdown("## ⚙️ Paramètres")
jeton_api  = st.sidebar.text_input("🔑 Jeton API Deriv", type="password")
marche     = st.sidebar.selectbox("📌 Marché", list(MARCHE_SYMBOLES.keys()))
symbole    = MARCHE_SYMBOLES[marche]
intervalle = st.sidebar.slider("⏱️ Intervalle (sec)", 3, 30, 5)
mode_reel  = st.sidebar.toggle("💸 Mode Réel (Argent)", value=False)

if mode_reel:
    st.sidebar.error("⚠️ MODE RÉEL ACTIVÉ — Argent réel engagé !")
else:
    st.sidebar.info("🔵 Mode Simulation — Aucun argent réel.")

st.sidebar.markdown("---")
col_a, col_b = st.sidebar.columns(2)

if col_a.button("▶️ Démarrer", use_container_width=True):
    if not jeton_api and mode_reel:
        st.sidebar.error("Jeton API requis en mode réel.")
    else:
        st.session_state.bot_actif = True
        st.sidebar.success("Bot démarré !")

if col_b.button("⏹️ Arrêter", use_container_width=True):
    st.session_state.bot_actif = False
    st.sidebar.info("Bot arrêté.")

if st.sidebar.button("🔄 Réinitialiser les Stats", use_container_width=True):
    st.session_state.stats = {
        'profit': 0.0, 'victoires': 0,
        'pertes': 0, 'martingale': 0, 'logs': []
    }
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**📊 Limites de session**
- Stop Loss : `{STOP_LOSS}$`
- Take Profit : `{TAKE_PROFIT}$`
- Martingale max : `Niv. {MARTINGALE_MAX}`
""")


# ───────────────────────────────────────────
#  MOTEUR PRINCIPAL
# ───────────────────────────────────────────
if st.session_state.bot_actif:
    ph_statut.success(f"🟢 Bot actif sur **{marche}** — Cycle toutes les {intervalle}s")

    # Récupération + affichage graphique immédiat
    prix = recuperer_ticks(symbole, count=60)
    if isinstance(prix, list) and len(prix) > 0:
        st.session_state.prix_data = prix
        afficher_graphe(prix, marche)

        # Analyse en direct
        df      = pd.DataFrame({'close': prix})
        analyse = analyser_marche(df)
        if analyse["signal"]:
            ph_analyse.success(f"🎯 **{analyse['signal']}** — {analyse['raison']}")
        else:
            ph_analyse.info(f"⏳ {analyse['raison']}")
    else:
        erreur = prix.get("erreur", "Erreur inconnue") if isinstance(prix, dict) else "Pas de données"
        ph_analyse.error(f"❌ {erreur}")
        afficher_graphe(st.session_state.prix_data, marche)

    # Exécution du cycle complet
    rapport = executer_cycle(jeton_api, symbole, st.session_state.stats, mode_reel)
    st.session_state.last_action = rapport.get("message", "")

    # Arrêt automatique si limite atteinte
    if rapport["action"] in ("STOP_LOSS", "TAKE_PROFIT"):
        st.session_state.bot_actif = False
        if rapport["action"] == "STOP_LOSS":
            st.error(rapport["message"])
        else:
            st.success(rapport["message"])
    
    time.sleep(intervalle)
    st.rerun()

else:
    afficher_graphe(st.session_state.prix_data, marche)
    ph_statut.info("🔵 Bot en veille — Appuyez sur **Démarrer**.")
    if st.session_state.last_action:
        ph_analyse.info(f"Dernière action : {st.session_state.last_action}")


# ───────────────────────────────────────────
#  JOURNAL DE TRADING
# ───────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Journal de Trading")

if s['logs']:
    df_logs = pd.DataFrame(s['logs'])
    st.dataframe(df_logs, use_container_width=True, height=300)
else:
    st.info("Aucun trade enregistré. Démarrez le bot pour voir les résultats.")