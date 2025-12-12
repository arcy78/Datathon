# src/bcl_scrapper.py

import os
import csv
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# Importation des chemins sécurisés
# src/bcl_scrapper.py
# ...
# Au lieu de 'from src.security_config import ...'
from security_config import URL_ROOT, DOWNLOAD_DIR, LOG_FILE, SIZE_THRESHOLD
# ...
# Extensions de documents à capturer (doit être la liste étendue)
DOC_EXTS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".zip", ".txt"]

# Heuristiques de sections cibles pour la navigation
SECTION_KEYWORDS = [
    "/reglements_bcl/",
    "/circulaires_bcl/",
    "/conditions_generales",
    "/loi_organique",
    "/avis",
    "target",
    "/conditions"
]

# --- Fonctions Utilitaires ---

def is_document_href(href: str) -> bool:
    if not href:
        return False
    hl = href.lower().split("?")[0]
    return any(hl.endswith(ext) for ext in DOC_EXTS)

def is_section_href(href: str) -> bool:
    if not href:
        return False
    hl = href.lower()
    return any(k in hl for k in SECTION_KEYWORDS)

def filename_from_url(url: str) -> str:
    name = url.split("/")[-1].split("?")[0].strip()
    return name or "document_bcl"

def log_entry(section_url, file_url, filename, mime, size_bytes, last_modified, clen, status):
    """Écrit une ligne dans le fichier de log CSV."""
    # S'assurer que le fichier log existe
    if not os.path.exists(LOG_FILE):
         with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "downloaded_at",
                "section_url",
                "file_url",
                "filename",
                "mime_type",
                "size_bytes",
                "last_modified",
                "content_length_header",
                "status"
            ])
            
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            section_url,
            file_url,
            filename,
            mime or "",
            size_bytes if size_bytes is not None else "",
            last_modified or "",
            clen or "",
            status
        ])


def collect_links_on_page(page, base_url):
    """Collecte les liens de sections et de documents sur une page."""
    hrefs = page.locator("a[href]").evaluate_all("els => els.map(e => e.getAttribute('href'))")
    hrefs = [urljoin(base_url, h) for h in hrefs if h]
    
    section_links = [h for h in hrefs if is_section_href(h) or h.lower().endswith(".html")]
    document_links = [h for h in hrefs if is_document_href(h)]
    
    section_links = list(dict.fromkeys(section_links))
    document_links = list(dict.fromkeys(document_links))
    return section_links, document_links


def head_metadata(api_ctx, url: str):
    """Utilise Playwright APIRequestContext pour récupérer les headers."""
    try:
        resp = api_ctx.head(url)
        mime = resp.headers.get("content-type")
        last_mod = resp.headers.get("last-modified")
        clen = resp.headers.get("content-length")
        return mime, last_mod, clen
    except Exception:
        return None, None, None


def download_via_browser(page, file_url: str, dest_path: str):
    """Déclenche le téléchargement du fichier via la simulation de navigateur."""
    # La méthode .expect_download est cruciale pour contourner les protections
    with page.expect_download() as dl_info:
        # Utiliser window.open ou une navigation simple
        page.evaluate(f"window.open('{file_url}', '_blank')") 
    download = dl_info.value
    download.save_as(dest_path)


# --- Fonction Principale d'Orchestration du Scraping ---

def crawl_and_download():
    """
    Exécute le processus de web scraping récursif et de téléchargement.
    Retourne le nombre total de fichiers téléchargés avec succès.
    """
    # Ne pas appeler ensure_dirs ici, Streamlit le fait au démarrage.

    with sync_playwright() as p:
        # Utilisation de l'APIRequestContext pour la vérification des métadonnées (HEAD)
        api_ctx = p.request.new_context()

        # Le contexte du navigateur pour le scraping et le téléchargement
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(URL_ROOT, wait_until="domcontentloaded")

        root_sections, root_docs = collect_links_on_page(page, URL_ROOT)

        to_visit = list(root_sections)
        visited_pages = set()
        total_ok = 0

        # Fusionner documents racine et ceux trouvés durant la navigation
        all_docs_to_download = list(root_docs)

        # 1. Exploration et collecte des liens
        while to_visit:
            section_url = to_visit.pop(0)
            if section_url in visited_pages:
                continue
            visited_pages.add(section_url)

            parsed = urlparse(section_url)
            if "bcl.lu" not in parsed.netloc or "/documents_nationaux/" not in section_url:
                continue

            try:
                page.goto(section_url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                continue

            sec_sections, sec_docs = collect_links_on_page(page, section_url)
            
            # Ajouter les nouveaux liens de documents à la liste globale
            for doc in sec_docs:
                if doc not in all_docs_to_download:
                    all_docs_to_download.append(doc)
            
            # Ajouter les nouvelles sections à visiter
            for s in sec_sections:
                if s not in visited_pages and s not in to_visit:
                    to_visit.append(s)
            
            # Politesse: attendre un peu entre les pages de navigation
            time.sleep(1)

        # 2. Téléchargement de tous les documents collectés
        
        for doc_url in all_docs_to_download:
            filename = filename_from_url(doc_url)
            dest = os.path.join(DOWNLOAD_DIR, filename)

            # Vérification de l'existence (important si le log est effacé mais pas les fichiers)
            if os.path.exists(dest):
                continue
            
            # Utilisation de l'API pour récupérer les métadonnées avant de télécharger
            mime, last_mod, clen = head_metadata(api_ctx, doc_url)
            
            try:
                # Téléchargement via le navigateur
                download_via_browser(page, doc_url, dest)
                size = os.path.getsize(dest)
                
                if size < SIZE_THRESHOLD:
                    os.remove(dest)
                    log_entry(URL_ROOT, doc_url, filename, mime, size, last_mod, clen, "fail_too_small")
                else:
                    log_entry(URL_ROOT, doc_url, filename, mime, size, last_mod, clen, "ok")
                    total_ok += 1
            except Exception as e:
                log_entry(URL_ROOT, doc_url, filename, mime, None, last_mod, clen, f"error:{e}")
                
            # Politesse: attendre entre les téléchargements
            time.sleep(1.5)

        browser.close()
        return total_ok

if __name__ == "__main__":
    # Ce bloc sera utilisé uniquement pour les tests unitaires
    # Tu dois utiliser Streamlit pour lancer la fonction
    from src.security_config import ensure_secure_dirs
    ensure_secure_dirs()
    print(f"Téléchargés : {crawl_and_download()}")