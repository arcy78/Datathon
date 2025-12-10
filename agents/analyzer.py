import pandas as pd
from utils.logger import setup_logger

logger = setup_logger()

class AnalyzerAgent:
    def __init__(self, key_file="Key Words.csv"):
        self.key_file = key_file
        self.keywords = self._load_keys()

    def _load_keys(self):
        try:
            if self.key_file.endswith('xlsx'):
                df = pd.read_excel(self.key_file)
            else:
                df = pd.read_csv(self.key_file)
            words = [str(x).lower().strip() for x in df.values.flatten() if str(x) != 'nan']
            return list(set(words))
        except:
            return ["risk", "compliance"] # Fallback

    def analyze(self, text):
        if not text: return 0, []
        text_lower = text.lower()
        found = [k for k in self.keywords if k in text_lower]
        return len(found), found