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
        """Dispatche vers JSON ou HTML selon la config."""
        stype = source_config.get('type', 'html')
        if stype == 'json':
            return self._fetch_from_json(source_config)
        else:
            return self._fetch_from_html(source_config)

    def _fetch_from_json(self, config):
        name = config['name']
        url = config['url']
        base = config.get('base_url_for_files', '')
        logger.info(f"--- [API] Connexion à {name} ---")

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            links = []
            # Adaptation structure JSON BCL
            items = data if isinstance(data, list) else data.get('results', [])
            
            for item in items:
                # Cherche le chemin dans différentes clés possibles
                path = item.get('path') or item.get('url') or item.get('link')
                if path and path.endswith('.pdf'):
                    full_url = urljoin(base, path)
                    if SecurityManager.validate_url(full_url, config['domain']):
                        links.append(full_url)
            
            limit = config.get('limit', 3)
            logger.info(f"[{name}] {len(links)} PDF trouvés (API).")
            return list(set(links))[:limit]
        except Exception as e:
            logger.error(f"Erreur API {name}: {e}")
            return []

    def _fetch_from_html(self, config):
        name = config['name']
        url = config['url']
        domain = config['domain']
        logger.info(f"--- [WEB] Connexion à {name} ---")

        if not SecurityManager.validate_url(url, domain):
            return []

        try:
            resp = requests.get(url, timeout=15)
            soup = BeautifulSoup(resp.content, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.lower().strip().endswith('.pdf'):
                    full = urljoin(url, href)
                    if domain in full:
                        links.append(full)
            limit = config.get('limit', 3)
            return list(set(links))[:limit]
        except Exception as e:
            logger.error(f"Erreur Web {name}: {e}")
            return []

    def download_file(self, url):
        try:
            name = SecurityManager.sanitize_filename(url.split('/')[-1])
            path = os.path.join(self.download_folder, name)
            if os.path.exists(path): return path
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
            return path
        except Exception as e:
            logger.error(f"Download Error: {e}")
            return None