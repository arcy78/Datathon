import os
from groq import Groq
from utils.logger import setup_logger

# Note : On n'importe JAMAIS orchestration ici.

logger = setup_logger()

class TranslationAgent:
    def __init__(self):
        # Récupération de la clé API
        api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
                logger.info("Agent de traduction (Groq) initialisé.")
            except Exception as e:
                logger.error(f"Erreur init Groq: {e}")
        else:
            logger.warning("⚠️ Clé GROQ_API_KEY manquante. Traduction désactivée.")

    def translate(self, text, target_language):
        """
        Utilise Groq (Llama 3) pour traduire le texte rapidement.
        """
        # Sécurité : si texte vide
        if not text or len(text.strip()) < 5:
            return text or ""
        
        # Pas de traduction si la langue cible est l'anglais
        if target_language.lower() in ["english", "en"]:
            return text

        if not self.client:
            return f"[Non Traduit - Clé Manquante] {text[:50]}..."

        logger.info(f"Appel à Groq pour traduction vers : {target_language}")

        try:
            # Prompt optimisé pour la vitesse
            system_prompt = (
                f"You are a professional translator. Translate the input text to {target_language}. "
                "Output ONLY the translation. No polite phrases, no intro."
            )

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text[:6000]} # Limite pour éviter les erreurs de token
                ],
                model="llama3-70b-8192", 
                temperature=0.1,
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            logger.error(f"Erreur Groq API: {e}")
            return f"[Erreur] {text[:100]}..."