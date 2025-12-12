import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from config import DOWNLOAD_FOLDER
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger()

class ScraperAgent:
    def __init__(self):
        self.download_folder = DOWNLOAD_FOLDER
        os.makedirs(self.download_folder, exist_ok=True)
        # Headers pour ressembler à un vrai navigateur
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_documents(self, source_config):
        """Dispatche vers la logique BCL."""
        if source_config.get('type') == 'bcl_web_scraping':
            return self._crawl_bcl_site(source_config)
        return []

    def _crawl_bcl_site(self, config):
        base_url = config['url_index']
        domain = config['domain']
        limit = config.get('limit', 20)
        
        logger.info(f"--- [CRAWLER BCL] Démarrage sur : {base_url} ---")
        
        documents_found = []
        visited_urls = set()
        
        try:
            # ETAPE 1 : Récupérer la page d'accueil pour trouver les "Onglets" (Sous-sections)
            resp = requests.get(base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # On cherche les liens dans le menu de navigation ou le contenu principal
            # Pour la BCL, les sections sont souvent dans <div class="content"> ou les menus latéraux
            sub_pages = []
            
            # On ajoute la page principale elle-même
            sub_pages.append(base_url)
            
            # Exploration simple : on prend tous les liens qui contiennent "/reporting_reglementaire/"
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(base_url, href)
                
                # On ne garde que les sous-pages du reporting, pas tout le site
                if "/reporting_reglementaire/" in full_url and domain in full_url:
                    if not full_url.endswith('.pdf'): # On ne veut pas les PDF tout de suite
                        sub_pages.append(full_url)
            
            # Dédoublonnage
            sub_pages = list(set(sub_pages))
            logger.info(f"Sous-sections identifiées : {len(sub_pages)}")

            # ETAPE 2 : Visiter chaque sous-section pour trouver les PDFs
            for page_url in sub_pages:
                if len(documents_found) >= limit: break
                if page_url in visited_urls: continue
                
                visited_urls.add(page_url)
                logger.info(f"Scraping section : {page_url}")
                
                try:
                    sub_resp = requests.get(page_url, headers=self.headers, timeout=10)
                    sub_soup = BeautifulSoup(sub_resp.content, 'html.parser')
                    
                    for a in sub_soup.find_all('a', href=True):
                        if len(documents_found) >= limit: break
                        
                        href = a['href']
                        if href.lower().strip().endswith('.pdf'):
                            pdf_url = urljoin(page_url, href)
                            
                            # Téléchargement
                            local_path = self._download_pdf(pdf_url)
                            if local_path:
                                documents_found.append(local_path)
                                
                except Exception as e:
                    logger.warning(f"Erreur sur la section {page_url}: {e}")
                    
            logger.info(f"Total documents récupérés : {len(documents_found)}")
            return documents_found

        except Exception as e:
            logger.error(f"Erreur critique Crawler: {e}")
            return []

    def _download_pdf(self, url):
        """Télécharge un PDF et retourne son chemin local."""
        try:
            filename = url.split('/')[-1]
            # Nettoyage nom fichier
            clean_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ('-', '_', '.')])
            # Ajout timestamp pour éviter doublons
            path = os.path.join(self.download_folder, clean_name)
            
            # Si fichier existe déjà, on ne retélécharge pas (sauf si vide)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path

            with requests.get(url, headers=self.headers, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            
            logger.info(f"PDF téléchargé : {clean_name}")
            return path
        except Exception as e:
            logger.error(f"Echec download {url}: {e}")
            return None