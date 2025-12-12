# main_app.py
import streamlit as st
import os

# --- IMPORT DU LOGGER ---
try:
    from logger import setup_logger
except ImportError:
    import logging
    def setup_logger():
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("Fallback")

# ==========================================
# 1. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="Orchestrateur AI BCL",
    page_icon="🤖",
    layout="wide"
)

# --- INITIALISATION DU LOGGER ---
if "logger" not in st.session_state:
    st.session_state.logger = setup_logger()
logger = st.session_state.logger
logger.info("=== Démarrage de l'application Streamlit ===")

# ==========================================
# 2. IMPORTS ET GESTION DES ERREURS
# ==========================================
try:
    from translations import TRANSLATIONS
except ImportError:
    st.error("⚠️ ERREUR CRITIQUE : Le fichier `translations.py` est introuvable.")
    st.stop()

# Import des Agents
try:
    import agent_ai1_scrapper as agent1 
    import agent_ai2_notif as agent2
    import agent_ai3_traducteur as agent3
    import agent_ai4_email as agent4
except ImportError as e:
    st.warning(f"⚠️ Certains agents n'ont pas pu être chargés : {e}")

# ==========================================
# 3. DESIGN & CSS
# ==========================================
st.markdown(
    """
    <style>
        :root { --sg-red: #E3000F; --sg-dark: #333333; --sg-light-bg: #f8f9fa; }
        section[data-testid="stSidebar"] * { color: var(--sg-dark) !important; }
        .stButton > button { color: white !important; background-color: var(--sg-red); border-color: var(--sg-red); }
        h1, h2, h3 { color: var(--sg-red) !important; }
        section[data-testid="stSidebar"] { background-color: var(--sg-light-bg); border-right: 1px solid #e0e0e0; }
        div[data-testid="stSidebar"] .stRadio div[aria-selected="true"] { background-color: #FEE0E0; border-radius: 5px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 4. GESTION DE LA LANGUE & SESSION
# ==========================================
if 'language' not in st.session_state:
    st.session_state.language = "French"

# Sélecteur de langue dans la sidebar
with st.sidebar:
    st.image("sg_logo.png", width=200) # Assure-toi que le chemin est bon
    st.session_state.language = st.selectbox(
        "Language / Langue", 
        ["French", "English", "Spanish", "German"],
        index=0
    )

# Récupération des textes selon la langue
T = TRANSLATIONS[st.session_state.language]

# ==========================================
# 5. SYSTÈME DE LOGIN (Simplifié)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login_screen():
    st.title(T["login_title"])
    st.info(T["login_info"])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button(T["login_button"]):
            # Login fictif pour la démo
            if username and password: 
                st.session_state.authenticated = True
                st.session_state.user_email = "utilisateur@sg.com" # Exemple
                st.success(T["login_success"])
                st.rerun()
            else:
                st.error("Identifiants incorrects")

if not st.session_state.authenticated:
    login_screen()
    st.stop() # On arrête l'exécution ici si pas connecté

# ==========================================
# 6. NAVIGATION PRINCIPALE
# ==========================================
with st.sidebar:
    st.write(f"👤 {T['user_connected']} **{st.session_state.get('user_email', 'Admin')}**")
    st.markdown("---")
    
    menu_options = [
        T["sidebar_home"],
        T["sidebar_visu"],
        T["sidebar_agent1"],
        T["sidebar_agent2"],
        T["sidebar_agent3"],
        T["sidebar_agent4"]
    ]
    
    choice = st.radio("Navigation", menu_options)

# ==========================================
# 7. ROUTAGE DES PAGES
# ==========================================

if choice == T["sidebar_home"]:
    st.title(T["home_title"])
    st.subheader(T["home_subtitle"])
    st.markdown(f"""
    ### {T['pipeline_overview']}
    1. **{T['pipe_step1']}**
    2. **{T['pipe_step2']}**
    3. **{T['pipe_step3']}**
    4. **{T['pipe_step4']}**
    """)
    st.info(T["start_info_msg"])

elif choice == T["sidebar_visu"]:
    st.title(T["visual_title"])
    st.write("Graphiques et statistiques ici...")

elif choice == T["sidebar_agent1"]:
    # Appel de l'Agent 1
    # Attention: agent_ai1_scrapper a une fonction run_scrapping_agent() qui retourne un booléen
    st.title(T["sidebar_agent1"])
    if st.button("Lancer le Scrapping"):
        success = agent1.run_scrapping_agent()
        if success:
            st.success("Scrapping terminé avec succès !")
        else:
            st.error("Erreur lors du scrapping.")

elif choice == T["sidebar_agent2"]:
    agent2.run_analysis_interface()

elif choice == T["sidebar_agent3"]:
    agent3.run_translation_interface()

elif choice == T["sidebar_agent4"]:
    agent4.run_email_agent_interface()