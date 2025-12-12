# src/security_config.py

import os
from pathlib import Path

# --- Gestion des chemins Sécurisés ---
# Le BASE_DIR est le répertoire racine du projet (un niveau au-dessus de 'src')
BASE_DIR = Path(__file__).resolve().parent.parent

# Dossiers de travail
DOWNLOAD_DIR = BASE_DIR / "data" / "BCL_Documents_Downloads"
LOG_FILE = BASE_DIR / "data" / "BCL_Documents_Log.csv"
TEMP_DIR = BASE_DIR / "tmp_secure" # Dossier pour fichiers temporaires (DuckDB, xlwings)

def ensure_secure_dirs():
    """Crée tous les dossiers nécessaires."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    # Assurer que le dossier 'data' existe pour le log
    os.makedirs(BASE_DIR / "data", exist_ok=True)

# --- Configuration Playwright ---
URL_ROOT = "https://www.bcl.lu/fr/cadre_juridique/documents_nationaux/index.html"
SIZE_THRESHOLD = 5000  # Seuil pour les fichiers non corrompus (en octets)

# --- Couleurs SGBL (Exemple pour l'UX/IX) ---
# Couleurs d'entreprise (à ajuster selon tes préférences précises)
SGBL_PRIMARY = "#CC0000" # Rouge dominant
SGBL_SECONDARY = "#0078D4" # Bleu (pour les accents)