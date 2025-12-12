# agent_ai1_scrapper.py
import os
import shutil
import sys
import subprocess
import time

# Ajoute le dossier courant au path pour les imports si nécessaire
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

try:
    from config import Config
    # On n'importe plus scrapper directement pour l'exécution, 
    # mais on a besoin de config pour les chemins.
except ImportError:
    Config = None

def run_scrapping_agent():
    """
    Agent 1 : Exécute le scrapping via un sous-processus isolé.
    Cela contourne le conflit 'Asyncio Loop' entre Streamlit et Playwright sur Windows.
    """
    if Config is None:
        print("ERREUR: Le fichier 'config.py' est manquant.")
        return False

    print("--- Démarrage de l'Agent AI 1 (Scrapping et Staging) ---")
    
    # 1. NETTOYAGE (Fait ici par l'orchestrateur)
    print(f"[1/3] Préparation du Staging : {Config.STAGING_DIR}")
    
    if os.path.exists(Config.STAGING_DIR):
        try:
            shutil.rmtree(Config.STAGING_DIR) 
        except OSError as e:
            print(f"[WARNING] Impossible de supprimer {Config.STAGING_DIR}. Erreur: {e}")
            return False
    os.makedirs(Config.STAGING_DIR, exist_ok=True)
    
    # 2. GÉNÉRATION D'UN LANCEUR TEMPORAIRE
    # Nous créons un petit script python temporaire qui va :
    # - Importer le scrapper
    # - Configurer le dossier de destination
    # - Lancer le crawl
    # Cela garantit que le scrapper tourne dans un processus "propre".
    
    launcher_code = f"""
import sys
import os
# Ajout du path courant
sys.path.append(r"{os.path.dirname(os.path.abspath(__file__))}")

import scrapper

# Injection de la configuration
print("--> Configuration du dossier cible : {Config.STAGING_DIR}")
scrapper.DOWNLOAD_DIR = r"{Config.STAGING_DIR}"

# Lancement
try:
    scrapper.crawl_and_download()
    print("--> Fin du process Scrapper.")
except Exception as e:
    print(f"--> ERREUR FATALE dans le sous-processus : {{e}}")
    sys.exit(1)
"""
    
    launcher_filename = "temp_scrapper_launcher.py"
    with open(launcher_filename, "w", encoding="utf-8") as f:
        f.write(launcher_code)
        
    print(f"[2/3] Lancement du processus isolé...")

    # 3. EXÉCUTION DU SOUS-PROCESSUS
    try:
        # On appelle python.exe pour exécuter notre lanceur temporaire
        result = subprocess.run(
            [sys.executable, launcher_filename],
            capture_output=True,
            text=True,
            encoding='utf-8' # Force l'encodage pour éviter les erreurs d'accent
        )
        
        # Affichage des logs du sous-processus dans la console Streamlit
        print("LOGS DU SCRAPPER :")
        print(result.stdout)
        
        if result.stderr:
            print("ERREURS DU SCRAPPER :")
            print(result.stderr)

        # Vérification du code de retour (0 = succès)
        if result.returncode == 0:
            print(f"[3/3] Téléchargement terminé avec succès dans {Config.STAGING_DIR}.")
            success = True
        else:
            print("[ERREUR] Le sous-processus a échoué.")
            success = False

    except Exception as e:
        print(f"ERREUR CRITIQUE lors du lancement du sous-processus : {e}")
        success = False
    
    finally:
        # Nettoyage du fichier lanceur temporaire
        if os.path.exists(launcher_filename):
            os.remove(launcher_filename)

    return success

if __name__ == "__main__":
    run_scrapping_agent()