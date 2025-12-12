# agents/analyzer.py
import pandas as pd
import os
from utils.logger import setup_logger

logger = setup_logger()

class AnalyzerAgent:
    def __init__(self, key_file="Key Words.csv"):
        self.key_file = key_file
        self.keywords = self._load_keys()

    def _load_keys(self):
        """Charge et nettoie les mots-clés depuis le CSV/Excel."""
        if not os.path.exists(self.key_file):
            logger.error(f"Fichier {self.key_file} introuvable.")
            return ["energy", "compliance", "window", "thermal"] # Fallback NREL context

        try:
            if self.key_file.endswith('xlsx'):
                df = pd.read_excel(self.key_file, header=None)
            else:
                try:
                    df = pd.read_csv(self.key_file, header=None, sep=None, engine='python')
                except:
                    df = pd.read_csv(self.key_file, header=None)
            
            # Aplatir et nettoyer
            raw_list = df.values.flatten()
            clean_keys = [str(x).lower().strip() for x in raw_list if str(x).lower() != 'nan' and len(str(x)) > 2]
            return list(set(clean_keys))
            
        except Exception as e:
            logger.error(f"Erreur chargement mots-clés: {e}")
            return ["error"]

    def analyze(self, text):
        """Cherche les correspondances."""
        if not text: return 0, []
        
        text_lower = text.lower()
        found = []
        for k in self.keywords:
            if k in text_lower:
                found.append(k)
        
        return len(found), list(set(found))