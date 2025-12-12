# agent_ai2_notif.py
import streamlit as st
import docx
import fitz  # PyMuPDF
import pandas as pd
import os
import re

# ==========================================
# CONFIGURATION
# ==========================================
DOCS_DIR = "BCL_Documents_Downloads"
KEYWORDS_FILE = "Key Words.csv"

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def read_keywords(keywords_csv_path):
    """Lit les mots-clés de la colonne C du CSV."""
    try:
        # On suppose le format : ID;Catégorie;MotClé
        keywords_df = pd.read_csv(keywords_csv_path, sep=';', encoding='utf-8')
        return keywords_df.iloc[:, 2].dropna().unique().tolist()
    except Exception as e:
        st.error(f"Erreur lecture mots-clés : {e}")
        return []

def extract_text(file_source, is_path=False):
    """Extrait le texte (simplifié pour la démo)."""
    try:
        if is_path:
            file_path = file_source
            if file_path.endswith(".pdf"):
                doc = fitz.open(file_path)
                return "".join([page.get_text() for page in doc])
            elif file_path.endswith(".docx"):
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            elif file_path.endswith(".txt"):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: return f.read()
            return ""
    except: return ""
    return ""

def search_keywords_and_summarize(directory_path, keywords):
    """
    Parcourt les documents et capture : Fichier, Mot-clé, Contexte.
    """
    results = []
    if not os.path.exists(directory_path):
        return pd.DataFrame()

    file_list = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    
    for filename in file_list:
        file_path = os.path.join(directory_path, filename)
        document_text = extract_text(file_path, is_path=True)
        
        if not document_text: continue

        keyword_found_in_file = False
        for kw in keywords:
            # Recherche insensible à la casse
            if re.search(re.escape(kw), document_text, re.IGNORECASE):
                # Extraction du contexte (100 caractères avant/après)
                match = re.search(r'(.{0,100}' + re.escape(kw) + r'.{0,100})', document_text, re.IGNORECASE | re.DOTALL)
                context = "..." + match.group(1).replace('\n', ' ') + "..." if match else "Contexte non extrait."
                
                # --- MODIFICATION ICI : Ajout explicite de la colonne Mot-clé ---
                results.append({
                    "Fichier": filename,
                    "Mot-clé Cible": kw,  # <--- La colonne demandée
                    "Extrait du Contexte": context,
                    "Statut": "Trouvé"
                })
                keyword_found_in_file = True
                # On break ici si on veut s'arrêter au premier mot-clé trouvé par fichier, 
                # sinon enlève le break pour tous les trouver.
                break 
        
        if not keyword_found_in_file:
             results.append({
                 "Fichier": filename, 
                 "Mot-clé Cible": "-", 
                 "Extrait du Contexte": "-", 
                 "Statut": "Aucun mot-clé"
             })
            
    return pd.DataFrame(results)

# ==========================================
# INTERFACE PRINCIPALE
# ==========================================

def run_analysis_interface():
    st.title("📊 Agent AI 2: Analyse & Extraction")
    st.markdown("---")

    keywords_list = read_keywords(KEYWORDS_FILE)
    
    # 1. Affichage du tableau des recherches (Ta demande précédente)
    if keywords_list:
        with st.expander("📋 Voir les Mots-clés surveillés (Recherches Keyword)", expanded=True):
            st.dataframe(pd.DataFrame(keywords_list, columns=["Recherches Keyword"]), use_container_width=True, height=150)

    if st.button("🚀 Lancer l'analyse"):
        with st.spinner("Recherche des contextes en cours..."):
            df_results = search_keywords_and_summarize(DOCS_DIR, keywords_list)
            st.session_state['analysis_results'] = df_results
            st.success("Analyse terminée !")
    
    if 'analysis_results' in st.session_state and not st.session_state['analysis_results'].empty:
        df = st.session_state['analysis_results']
        
        # Affichage des résultats filtrés
        found_df = df[df['Statut'] == 'Trouvé']
        
        st.subheader(f"Résultats ({len(found_df)} documents pertinents)")
        # On affiche bien la colonne Mot-clé Cible ici
        st.dataframe(
            found_df[['Fichier', 'Mot-clé Cible', 'Extrait du Contexte']], 
            use_container_width=True
        )

if __name__ == "__main__":
    run_analysis_interface()