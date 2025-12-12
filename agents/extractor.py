import os
from pypdf import PdfReader
from utils.logger import setup_logger

logger = setup_logger()

class ExtractionAgent:
    def extract_text(self, file_path):
        """Extrait le texte d'un PDF."""
        if not file_path or not os.path.exists(file_path):
            return ""

        logger.info(f"Extraction texte : {os.path.basename(file_path)}")
        
        # Fallback si ce n'est pas un PDF (ex: erreur download)
        if not file_path.endswith('.pdf'):
            return ""

        text_content = ""
        try:
            reader = PdfReader(file_path)
            # On lit max 5 pages pour la performance démo
            for i, page in enumerate(reader.pages):
                if i > 5: break 
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
            
            # Si le PDF est une image scannée (pas de texte), on met un warning
            if not text_content.strip():
                return "[PDF Image - OCR non activé pour cette démo]"
                
            return text_content
        except Exception as e:
            logger.error(f"Erreur lecture PDF {file_path}: {e}")
            return ""