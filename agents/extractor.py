from pypdf import PdfReader
from utils.logger import setup_logger

logger = setup_logger()

class ExtractionAgent:
    def extract_text(self, pdf_path):
        if not pdf_path: return ""
        logger.info(f"Extraction: {pdf_path}")
        content = ""
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                txt = page.extract_text()
                if txt: content += txt + "\n"
            return content
        except Exception as e:
            logger.error(f"Erreur PDF: {e}")
            return ""