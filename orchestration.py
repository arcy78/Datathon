import pandas as pd
from config import SOURCES_CONFIG
from agents.scraper import ScraperAgent
from agents.extractor import ExtractionAgent
from agents.translator import TranslationAgent
from agents.analyzer import AnalyzerAgent
from agents.notifier import NotificationAgent
from utils.logger import setup_logger
import os

logger = setup_logger()

def run_full_pipeline():
    """Exécute le workflow complet pour toutes les sources configurées."""
    results = []
    
    # Init Agents
    scraper = ScraperAgent()
    extractor = ExtractionAgent()
    translator = TranslationAgent()
    analyzer = AnalyzerAgent()
    notifier = NotificationAgent()

    logger.info(">>> DÉMARRAGE DU PIPELINE GLOBAL <<<")

    for source in SOURCES_CONFIG:
        # 1. Scraping (Scalable)
        pdf_urls = scraper.fetch_documents(source)
        
        for url in pdf_urls:
            # 2. Download
            local_path = scraper.download_file(url)
            if not local_path: continue

            # 3. Extraction
            raw_text = extractor.extract_text(local_path)

            # 4. Traduction
            eng_text = translator.translate_to_english(raw_text)

            # 5. Analyse
            score, matches = analyzer.analyze(eng_text)

            # Résultat structuré
            results.append({
                "source": source['name'],
                "file": os.path.basename(local_path),
                "url": url,
                "score": score,
                "matches": ", ".join(matches[:5]) # Top 5 mots
            })
            
            # Nettoyage temporaire (Sécurité)
            if os.path.exists(local_path):
                os.remove(local_path)

    # 6. Notification Groupée
    if results:
        notifier.send_report(results)
    
    logger.info(">>> FIN DU PIPELINE <<<")
    return pd.DataFrame(results)