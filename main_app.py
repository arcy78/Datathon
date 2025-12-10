import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv
from utils.security import SecurityManager
from orchestration import run_full_pipeline

# Chargement config
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Smart Regulatory Watch",
    page_icon="🛡️",
    layout="wide"
)

# CSS Personnalisé (Style SG GSC)
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; color: #E70011; font-weight: bold;}
    .sub-header {font-size: 1.5rem; color: #333;}
    .stButton>button {background-color: #E70011; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- GESTION LOGIN (Sécurité) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    input_pass = st.sidebar.text_input("Mot de passe Admin", type="password")
    if st.sidebar.button("Se connecter"):
        # Hash stocké dans le .env
        stored_hash = os.getenv("APP_PASSWORD_HASH")
        if SecurityManager.check_password(input_pass, stored_hash):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.sidebar.error("Accès Refusé.")

if not st.session_state.authenticated:
    st.markdown("<div class='main-header'>SG GSC Regulatory Watch</div>", unsafe_allow_html=True)
    st.info("Veuillez vous authentifier dans la barre latérale.")
    check_login()
    st.stop() # Arrête le script ici si pas connecté

# --- APPLICATION PRINCIPALE ---
st.sidebar.success("✅ Connecté (Admin)")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller vers", ["Dashboard", "Logs & Audit", "Configuration"])

if page == "Dashboard":
    st.markdown("<div class='main-header'>🛡️ Smart Regulatory Watch Tool</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Cliquez ci-dessous pour lancer l'orchestration des agents IA.")
        if st.button("▶ LANCER L'ANALYSE", use_container_width=True):
            with st.spinner('Les agents travaillent... (Scraping > Extraction > Traduction > Analyse)'):
                try:
                    df_results = run_full_pipeline()
                    st.session_state['last_results'] = df_results
                    st.success("Analyse terminée !")
                except Exception as e:
                    st.error(f"Erreur critique: {e}")

    with col2:
        if 'last_results' in st.session_state:
            df = st.session_state['last_results']
            if not df.empty:
                # Métriques
                total = len(df)
                risky = len(df[df['score'] > 0])
                m1, m2 = st.columns(2)
                m1.metric("Documents Analysés", total)
                m2.metric("Documents Critiques", risky, delta_color="inverse")
                
                st.subheader("Résultats Détaillés")
                # Filtres dynamiques
                score_filter = st.slider("Filtrer par score min.", 0, 10, 0)
                st.dataframe(df[df['score'] >= score_filter], use_container_width=True)
            else:
                st.warning("Aucun document trouvé ou analysé.")

elif page == "Logs & Audit":
    st.header("📝 Logs d'activité des Agents")
    if st.button("Rafraîchir les logs"):
        pass
    
    log_file = "activity.log"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            # Affiche les 50 dernières lignes
            st.text_area("Log Output", "".join(lines[-50:]), height=600)
    else:
        st.write("Aucun fichier de log pour le moment.")

elif page == "Configuration":
    st.header("⚙️ Configuration Système")
    st.write("Les sources sont gérées dans `config.py` pour la scalabilité.")
    
    # Affichage de la config chargée (Lecture seule)
    from config import SOURCES_CONFIG
    st.json(SOURCES_CONFIG)