import streamlit as st
import pandas as pd

# Configuration de la page pour un look large et pro
st.set_page_config(page_title="Kasaa Trade - Architecte Pro", layout="wide")

# --- STYLE CSS POUR FIGER LE HAUT ET AMÉLIORER LE DESIGN ---
st.markdown("""
    <style>
    /* Figer l'en-tête (Graphique et Stats) */
    [data-testid="stVerticalBlock"] > div:first-child {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 999;
        padding-bottom: 20px;
        border-bottom: 2px solid #f0f2f6;
    }
    
    /* Design des cartes de score */
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Couleurs pour les gains et pertes */
    .gain { color: #28a745; font-weight: bold; }
    .perte { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- EN-TÊTE FIXE ---
col1, col2 = st.columns([2, 1])

with col1:
    st.title("🚀 KASAÃ TRADE - ARCHITECTE PRO")
    # Ici ton graphique (st.line_chart ou autre)
    st.subheader("Analyse du Marché")
    # Simulation de graphique (remplace par tes données réelles)
    st.line_chart(st.session_state.get('history_df', pd.DataFrame({'Prix': [10, 12, 11, 15]})))

with col2:
    st.subheader("Performance Live")
    s = st.session_state.get('stats', {'profit': 0, 'gains': 0, 'pertes': 0, 'somme_gains': 0, 'somme_pertes': 0})
    
    # Calcul du verdict
    verdict = "✅ PROFIT" if s['profit'] > 0 else "❌ PERTE"
    
    st.metric("SOLDE NET", f"{s['profit']:.2f} $", delta=verdict)
    
    c_g, c_p = st.columns(2)
    c_g.metric("✅ Gains", s['gains'])
    c_p.metric("❌ Pertes", s['pertes'])

# --- RÉSUMÉ DÉTAILLÉ ---
st.markdown("---")
st.subheader("📊 Rapport de Session")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.write(f"💰 **Total encaissé :** :green[{s['somme_gains']:.2f} $]")
with col_b:
    st.write(f"📉 **Total perdu :** :red[{s['somme_pertes']:.2f} $]")
with col_c:
    status_color = "green" if s['profit'] > 0 else "red"
    st.write(f"📢 **Avis :** :{status_color}[{verdict if s['profit'] != 0 else 'EN ATTENTE'}]")

# --- TABLEAU D'HISTORIQUE ---
st.subheader("📜 Historique des Opérations")

# Exemple de structure de tableau améliorée
if 'logs' in st.session_state:
    df_logs = pd.DataFrame(st.session_state.logs)
    
    # On s'assure que les colonnes demandées existent
    # Colonnes : Heure | Marché | RSI | Type | Mise | Résultat | Gain/Perte Net
    st.dataframe(
        df_logs.style.applymap(lambda x: 'color: green' if x == 'X GAGNÉ' else ('color: red' if x == 'X PERDU' else ''), subset=['Résultat']),
        use_container_width=True
    )
else:
    st.info("En attente du premier trade...")