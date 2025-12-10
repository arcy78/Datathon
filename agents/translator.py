from deep_translator import GoogleTranslator
from utils.logger import setup_logger

logger = setup_logger()

class TranslationAgent:
    def translate_to_english(self, text):
        if not text: return ""
        # Limite API gratuite : ~4500 chars
        sample = text[:4500]
        try:
            return GoogleTranslator(source='auto', target='en').translate(sample)
        except Exception as e:
            logger.warning(f"Erreur Traduction: {e}")
            return sample # Retourne l'original si échec