# agent_ai3_traducteur.py
import streamlit as st
from transformers import pipeline
import pandas as pd
import os

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_MAP = {
    "Deutsch": "Helsinki-NLP/opus-mt-fr-de",
    "English": "Helsinki-NLP/opus-mt-fr-en",
    "Español": "Helsinki-NLP/opus-mt-fr-es",
    "Italiano": "Helsinki-NLP/opus-mt-fr-it",
}

@st.cache_resource
def get_translator(model):
    """Charge le modèle de traduction en cache pour éviter de le recharger à chaque fois."""
    return pipeline("translation", model=model)

# ==========================================
# LOGIQUE MÉTIER
# ==========================================

def translate_report_segments(report_df, lang_key):
    """
    Traduit les contextes trouvés tout en gardant la structure du tableau 
    (Fichier, Mot-clé, Contexte).
    """
    # 1. Filtrage : On ne traduit que les lignes où un mot-clé a été trouvé
    relevant = report_df[report_df['Statut'] == 'Trouvé'].copy()
    
    if relevant.empty:
        return pd.DataFrame()
    
    # 2. Chargement du modèle
    model_name = MODEL_MAP.get(lang_key, "Helsinki-NLP/opus-mt-fr-en")
    translator = get_translator(model_name)
    
    translated_texts = []
    
    # Barre de progression
    progress_bar = st.progress(0)
    total = len(relevant)
    
    # 3. Boucle de traduction (Utilisation de iterrows pour éviter les bugs de noms de colonnes)
    for i, (index, row) in enumerate(relevant.iterrows()):
        
        # Récupération sécurisée du texte source
        original_text = row.get("Extrait du Contexte", "")

        try:
            # Vérification que le texte est valide et non vide
            if isinstance(original_text, str) and len(original_text.strip()) > 0:
                # Traduction (On limite à 512 tokens pour éviter les erreurs de modèle)
                res = translator(original_text[:512])[0]['translation_text']
                translated_texts.append(res)
            else:
                translated_texts.append("") # Texte vide
        except Exception as e:
            translated_texts.append(f"[Erreur Traduction] {str(e)}")
        
        # Mise à jour de la barre
        progress_bar.progress((i + 1) / total)
            
    # 4. Ajout de la colonne traduction
    relevant['Traduction du Contexte'] = translated_texts
    
    # 5. Sélection et ordre des colonnes pour le rendu final
    cols_to_keep = ['Fichier', 'Mot-clé Cible', 'Traduction du Contexte', 'Extrait du Contexte']
    # On s'assure que toutes les colonnes existent
    final_cols = [c for c in cols_to_keep if c in relevant.columns]
    
    return relevant[final_cols]

# ==========================================
# INTERFACE STREAMLIT
# ==========================================

def run_translation_interface():
    st.title("🌍 Agent AI 3: Traducteur Intelligent")

    # --- 1. Récupération des données de l'Agent 2 ---
    if 'analysis_results' not in st.session_state:
        st.warning("⚠️ Aucune donnée d'analyse trouvée. Veuillez d'abord lancer l'Agent AI 2 (Analyse).")
        return

    df_source = st.session_state['analysis_results']
    
    # Vérification s'il y a des données pertinentes
    found_data = df_source[df_source['Statut'] == 'Trouvé'] if 'Statut' in df_source.columns else pd.DataFrame()

    st.header("1. Données reçues de l'Agent 2")
    st.write(f"Documents analysés : {len(df_source)}")
    
    if not found_data.empty:
        st.info(f"{len(found_data)} passages pertinents identifiés avec mots-clés.")
        # Affichage de la colonne 'Mot-clé Cible' comme demandé
        cols_preview = ['Fichier', 'Mot-clé Cible', 'Extrait du Contexte']
        st.dataframe(found_data[[c for c in cols_preview if c in found_data.columns]].head(), use_container_width=True)
    else:
        st.warning("L'analyse précédente n'a retourné aucun résultat pertinent (aucun mot-clé trouvé).")
        return # On arrête là si rien n'est trouvé

    st.write("---")

    # --- 2. Action de Traduction ---
    st.header("2. Traduction & Préparation du Rapport")
    
    lang_report = st.selectbox("Choisir la langue cible", list(MODEL_MAP.keys()))
    
    if st.button("Traduire les contextes identifiés ▶️", type="primary"):
        with st.spinner(f"Traduction en cours vers {lang_report}..."):
            final_df = translate_report_segments(df_source, lang_report)
            
        st.success("Traduction terminée !")
        
        st.subheader("📋 Résultat Final (Prêt pour l'Agent 4)")
        st.dataframe(final_df, use_container_width=True)
        
        # --- CRITIQUE : Passage de relais à l'Agent 4 ---
        # On sauvegarde ce tableau final dans le session_state sous le nom 'final_report'
        # C'est ce que l'Agent 4 (Email) va chercher.
        st.session_state['final_report'] = final_df
        
        st.info("💡 Les données sont prêtes. Vous pouvez maintenant passer à l'Agent 4 pour l'envoi par email.")

if __name__ == "__main__":
    run_translation_interface()