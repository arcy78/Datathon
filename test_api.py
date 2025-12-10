import streamlit as st
import requests
import pandas as pd
import json
import os
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="NREL BCL Data Explorer", layout="wide")

# --- FONCTIONS UTILITAIRES (BACKEND) ---

def fetch_api_data(base_url, pages_to_fetch=1):
    """
    Récupère les données de l'API avec gestion de la pagination simple.
    Note: L'API NREL BCL peut nécessiter une clé API ou paginer par 'page'.
    """
    all_results = []
    
    # Création du dossier data s'il n'existe pas
    if not os.path.exists('data'):
        os.makedirs('data')

    progress_bar = st.progress(0)
    
    for page in range(pages_to_fetch):
        # On ajoute le paramètre de page si l'API le supporte (paramètre fictif &page=X)
        # Pour cette URL spécifique, on va juste requêter l'URL brute donnée
        # Si l'API utilise un paramètre 'page', il faudrait l'ajouter : f"{base_url}&page={page}"
        
        try:
            response = requests.get(base_url)
            response.raise_for_status() # Lève une erreur si code != 200
            
            data = response.json()
            
            # L'API NREL renvoie souvent une structure du type {'result': [...]}
            # On essaie de trouver la liste des items
            if isinstance(data, list):
                items = data
            elif 'result' in data:
                items = data['result']
            else:
                # Si structure inconnue, on prend tout
                items = [data]
                
            all_results.extend(items)
            
            # Mise à jour barre de progression
            progress_bar.progress((page + 1) / pages_to_fetch)
            time.sleep(0.5) # Pause pour être gentil avec le serveur
            
        except requests.exceptions.RequestException as e:
            st.error(f"Erreur de connexion : {e}")
            break
            
    return all_results

def save_data(data, filename_prefix="nrel_data"):
    """Sauvegarde les données en JSON et CSV"""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # 1. Sauvegarde JSON (Raw data)
    json_path = f"data/{filename_prefix}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # 2. Sauvegarde CSV (Pour Excel/Pandas)
    df = pd.json_normalize(data)
    csv_path = f"data/{filename_prefix}_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    
    return json_path, csv_path, df

# --- INTERFACE UTILISATEUR (FRONTEND) ---

st.title("🔋 NREL Building Component Library - Extractor")
st.markdown("Cet outil interroge l'API NREL, affiche les résultats et sauvegarde les fichiers localement.")

# Zone de configuration dans la barre latérale
with st.sidebar:
    st.header("Configuration API")
    default_url = "https://bcl.nrel.gov/api/search/*.json?fq=bundle:measure&fq=openstudio_version:3.2.0&all_content_versions=1"
    api_url = st.text_area("URL de l'API", value=default_url, height=100)
    
    # Optionnel : Nombre d'appels (si pagination nécessaire)
    # st.info("Note : L'URL fournie semble être une recherche globale.")
    
    launch_btn = st.button("🚀 Lancer l'extraction", type="primary")

# Zone principale
if launch_btn:
    with st.spinner('Interrogation de l\'API en cours...'):
        # 1. Récupération
        results = fetch_api_data(api_url)
        
        if results:
            st.success(f"Succès ! {len(results)} éléments récupérés.")
            
            # 2. Sauvegarde et Transformation
            json_file, csv_file, df = save_data(results)
            
            # 3. Affichage des données
            st.subheader("📊 Aperçu des données")
            st.dataframe(df, use_container_width=True)
            
            # 4. Liens de téléchargement
            col1, col2 = st.columns(2)
            with col1:
                with open(json_file, "r") as f:
                    st.download_button("📥 Télécharger JSON", f, file_name="data.json")
            with col2:
                with open(csv_file, "r") as f:
                    st.download_button("📥 Télécharger CSV", f, file_name="data.csv")
            
            st.info(f"Fichiers sauvegardés localement dans :\n- `{json_file}`\n- `{csv_file}`")
            
        else:
            st.warning("L'API n'a renvoyé aucun résultat ou une liste vide.")