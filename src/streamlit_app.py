# src/streamlit_app.py

import sys
import os
from pathlib import Path

# --- MANIPULATION DU CHEMIN (CORRECTIF IMPORT) ---
# Ajoute la racine du projet (D:\Datathon) au chemin de recherche des modules.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
# --------------------------------------------------

import streamlit as st
import pandas as pd
import asyncio 
from transformers import pipeline

# Importation des modules locaux (IMPORTATION ABSOLUE)
from src.security_config import SGBL_PRIMARY, SGBL_SECONDARY, LOG_FILE, ensure_secure_dirs
from src.bcl_scrapper import crawl_and_download 
from src.doc_translator import MODEL_MAP, dispatch_file_for_translation


# 🚨 CORRECTIF CRUCIAL POUR PLAYWRIGHT SUR WINDOWS (asyncio/subprocess fix) 🚨
# Définit une politique de gestion de boucle d'événements plus compatible
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    pass 
# -----------------------------------------------------------------------------


# ==================================
# 1. Configuration et UX/IX
# ==================================

def configure_streamlit():
    """Applique le thème SGBL et la configuration de base."""
    st.set_page_config(
        page_title="BCL Regulator Data Pipeline", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # Style personnalisé (CSS) pour les couleurs SGBL
    st.markdown(f"""
        <style>
        .stButton>button {{
            background-color: {SGBL_PRIMARY};
            color: white;
            border-radius: 5px;
            border-color: {SGBL_PRIMARY};
        }}
        .stButton>button:hover {{
            background-color: {SGBL_SECONDARY};
            border-color: {SGBL_SECONDARY};
            color: white;
        }}
        .stSuccess, .stInfo, .stWarning, .stError {{
            border-radius: 8px;
            padding: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)
    st.title("🏦 Pipeline de Données Réglementaires BCL")
    st.markdown("---")


# ==================================
# 2. Fonctions d'Orchestration
# ==================================

def run_scrapping():
    """Lance le Scrapper Playwright et logue le résultat."""
    ensure_secure_dirs() 
    
    with st.spinner("Démarrage du Scrapping Playwright (Mode headless)... Patientez, cela peut prendre du temps..."):
        try:
            ok_count = crawl_and_download() 
            st.success(f"✅ Scrapping terminé ! {ok_count} fichiers téléchargés/mis à jour.")
        except Exception as e:
            st.error(f"❌ Erreur critique de Scrapping : {e}")

# ==================================
# 3. Visualisation (Métadonnées & Logger)
# ==================================

def display_metadata_and_logs():
    """Affiche les métadonnées des fichiers téléchargés (Logger sur Streamlit)."""
    st.subheader("🔍 Étape 2 : Inspection des Métadonnées & Logs (Logger Streamlit)")
    
    if not os.path.exists(LOG_FILE):
        st.warning("Aucun historique de log trouvé. Veuillez d'abord exécuter le Scrapper.")
        return

    try:
        df = pd.read_csv(LOG_FILE, encoding='utf-8') 
        
        df_display = df.rename(columns={'downloaded_at': 'Date', 'filename': 'Fichier', 'status': 'Statut', 'size_bytes': 'Taille (o)'})
        df_display = df_display[['Date', 'Fichier', 'Statut', 'Taille (o)', 'last_modified', 'file_url']]
        df_display['Taille (KB)'] = (df_display['Taille (o)'] / 1024).round(2)
        
        success_count = df['status'].eq('ok').sum()
        fail_count = df['status'].str.contains('fail|error', na=False).sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Fichiers OK", success_count)
        col2.metric("Échecs/Erreurs", fail_count)
        total_size = df['size_bytes'].sum()
        col3.metric("Taille Totale", f"{total_size / (1024**2):.2f} MB" if total_size > 0 else "0.00 MB")

        st.dataframe(df_display, use_container_width=True, height=350,
                     column_order=("Date", "Fichier", "Statut", "Taille (KB)", "last_modified", "file_url"))
        
    except pd.errors.EmptyDataError:
        st.warning("Le fichier de log est vide. Aucune donnée à afficher.")
    except Exception as e:
        st.error(f"Erreur lors de la lecture du log : {e}")


# ==================================
# 4. Traduction
# ==================================

def setup_translation_ui():
    st.subheader("📦 Étape 3 : Post-Traitement et Traduction")

    col_man, col_auto = st.columns(2)
    
    with col_man:
        st.markdown("##### Traduction de Fichier Manuelle")
        target_lang = st.selectbox("Langue cible", list(MODEL_MAP.keys()), key="man_lang")
        uploaded = st.file_uploader("Uploader un document", type=["pdf", "docx", "txt", "xls", "xlsx", "csv", "zip"], key="man_upload")

        if uploaded:
            model_name = MODEL_MAP[target_lang]
            st.info(f"Modèle : {model_name}")
            
            @st.cache_resource
            def load_model(name):
                return pipeline("translation", model=name)

            translator = load_model(model_name)
            file_bytes = uploaded.read()
            
            try:
                with st.spinner('Traduction en cours...'):
                    output, fname, mime, count = dispatch_file_for_translation(file_bytes, uploaded.name, translator) 

                st.success(f"Terminé ! ({target_lang})")
                
                if count > 1:
                    st.markdown(f"**{count}** documents internes (dans le ZIP) ont été traduits avec succès.")
                elif count == 1:
                    st.markdown(f"**1** fichier a été traduit avec succès.")
                    
                st.download_button("Télécharger", data=output, file_name=fname, mime=mime)

            except Exception as e:
                st.error(f"Erreur lors de la traduction : {e}")

    with col_auto:
        st.markdown("##### Traduction de Lot (Lot de fichiers BCL)")
        st.warning("La traduction automatique de lot n'est pas encore optimisée pour la scalabilité sur Streamlit et nécessite une file d'attente (comme Celery).")
        st.button("Lancer la Traduction Automatique de Lot", disabled=True)


# ==================================
# 5. Point d'entrée principal
# ==================================

def main():
    # 0. Initialisation des dossiers sécurisés
    ensure_secure_dirs() 
    
    configure_streamlit()
    
    st.subheader("⚙️ Étape 1 : Téléchargement des Réglementations BCL")
    if st.button("Lancer le Scrapper Playwright"):
        run_scrapping()
    
    st.markdown("---")
    display_metadata_and_logs()
    
    st.markdown("---")
    setup_translation_ui()

# Pour lancer l'application Streamlit
if __name__ == "__main__":
    main()