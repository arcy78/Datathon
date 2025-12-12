# config.py

import os

class Config:
    # Répertoires principaux
    PROD_DIR = "BCL_Documents_Downloads"
    STAGING_DIR = "BCL_Temp_Staging"
    REPORT_DIR = "BCL_Reports"
    
    # Fichiers principaux
    KEYWORDS_FILE = "Key Words.csv"
    STATE_FILE = os.path.join(PROD_DIR, "state.json")
    LOG_FILE = "BCL_Documents_Log.csv" 

    # Assurez-vous que les répertoires existent
    @staticmethod
    def ensure_directories_exist():
        os.makedirs(Config.PROD_DIR, exist_ok=True)
        os.makedirs(Config.STAGING_DIR, exist_ok=True)
        os.makedirs(Config.REPORT_DIR, exist_ok=True)

Config.ensure_directories_exist()