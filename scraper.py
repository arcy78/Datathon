import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from utils.logger import setup_logger
from utils.security import SecurityManager

logger = setup_logger()

class ScraperAgent:
    def __init__(self):
        self.download_folder = "temp_downloads"
        os.makedirs(self.download_folder, exist_ok=True)

    def fetch_documents(self, source_config):
        """
        Dispatche vers la bonne méthode selon le type de source (API JSON ou Page HTML).
        """
        source_type = source_config.get('type', 'html') # Par défaut HTML
        
        if source_type == 'json':
            return self._fetch_from_json(source_config)
        else:
            return self._fetch_from_html(source_config)

    def _fetch_from_json(self, config):
        """Traitement spécifique pour l'API BCL (ou autres APIs JSON)."""
        name = config['name']
        url = config['url']
        base_domain = config.get('base_url_for_files', config['url']) # Pour reconstruire le lien complet
        
        logger.info(f"--- [API MODE] Récupération JSON pour : {name} ---")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pdf_links = []
            
            # Adaptation spécifique à la structure JSON de la BCL
            # Le JSON BCL renvoie souvent une liste d'objets. 
            # On suppose ici une itération sur une liste.
            # Note: Il faudra peut-être ajuster selon la structure exacte (clé 'path', 'url', 'link'?)
            items = data if isinstance(data, list) else data.get('results', [])
            
            for item in items:
                # On cherche le champ qui contient le chemin du fichier
                # Souvent 'path', 'url' ou 'jcr:content'
                file_path = item.get('path') or item.get('url') or item.get('link')
                
                if file_path and file_path.endswith('.pdf'):
                    full_url = urljoin(base_domain, file_path)
                    
                    if SecurityManager.validate_url(full_url, config['domain']):
                        pdf_links.append(full_url)
            
            # Limite
            limit = config.get('limit', 3)
            logger.info(f"[{name}] {len(pdf_links)} PDFs trouvés via API.")
            return pdf_links[:limit]

        except Exception as e:
            logger.error(f"Erreur API JSON {name}: {e}")
            return []

    def _fetch_from_html(self, config):
        """Le scraping classique (BeautifulSoup) pour les sites sans API (ex: BCE)."""
        name = config['name']
        url = config['url']
        allowed_domain = config['domain']
        
        logger.info(f"--- [HTML MODE] Scraping pour : {name} ---")
        
        if not SecurityManager.validate_url(url, allowed_domain):
            return []

        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.lower().strip().endswith('.pdf'):
                    full_url = urljoin(url, href)
                    if allowed_domain in full_url:
                        pdf_links.append(full_url)
            
            limit = config.get('limit', 3)
            return list(set(pdf_links))[:limit]

        except Exception as e:
            logger.error(f"Erreur Scraping HTML {name}: {e}")
            return []

    def download_file(self, url):
        # Méthode inchangée (voir bloc précédent)
        try:
            local_filename = url.split('/')[-1]
            safe_filename = SecurityManager.sanitize_filename(local_filename)
            path = os.path.join(self.download_folder, safe_filename)
            if os.path.exists(path): return path
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            return path
        except Exception as e:
            logger.error(f"Erreur download: {e}"); return None