# pip install playwright
# playwright install

import os
import csv
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

URL_ROOT = "https://www.bcl.lu/fr/cadre_juridique/documents_nationaux/index.html"
DOWNLOAD_DIR = "BCL_Documents_Downloads"
LOG_FILE = "BCL_Documents_Log.csv"
SIZE_THRESHOLD = 5000  # éviter les pages d’erreur ~456 octets

# Extensions de documents à capturer
DOC_EXTS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".zip", ".txt"]

# Heuristiques de sections cibles (on reste large)
SECTION_KEYWORDS = [
    "/reglements_bcl/",
    "/circulaires_bcl/",
    "/conditions_generales",
    "/loi_organique",
    "/avis",
    "target",
    "/conditions"
]


def is_document_href(href: str) -> bool:
    if not href:
        return False
    hl = href.lower()
    return any(ext in hl for ext in DOC_EXTS)


def is_section_href(href: str) -> bool:
    if not href:
        return False
    hl = href.lower()
    return any(k in hl for k in SECTION_KEYWORDS)


def filename_from_url(url: str) -> str:
    name = url.split("/")[-1].split("?")[0].strip()
    return name or "document_bcl"


def ensure_dirs():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
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


def log_entry(section_url, file_url, filename, mime, size_bytes, last_modified, clen, status):
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
    # Récupère tous les href visibles
    hrefs = page.locator("a[href]").evaluate_all("els => els.map(e => e.getAttribute('href'))")
    hrefs = [urljoin(base_url, h) for h in hrefs if h]
    # Sépare en (sections) et (documents)
    section_links = [h for h in hrefs if is_section_href(h) or h.lower().endswith(".html")]
    document_links = [h for h in hrefs if is_document_href(h)]
    # Déduplication
    section_links = list(dict.fromkeys(section_links))
    document_links = list(dict.fromkeys(document_links))
    return section_links, document_links


def head_metadata(api_ctx, url: str):
    """Utilise Playwright APIRequestContext pour récupérer les headers (Last-Modified, Content-Type...)."""
    try:
        resp = api_ctx.head(url)
        mime = resp.headers.get("content-type")
        last_mod = resp.headers.get("last-modified")
        clen = resp.headers.get("content-length")
        return mime, last_mod, clen
    except Exception:
        return None, None, None


def download_via_browser(page, file_url: str, dest_path: str):
    # Important: ne pas utiliser page.goto pour les PDF; on déclenche une ouverture/fichier via window.open
    with page.expect_download() as dl_info:
        page.evaluate(f"window.open('{file_url}', '_blank')")
    download = dl_info.value
    download.save_as(dest_path)


def crawl_and_download():
    ensure_dirs()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Contexte API pour HEAD
        api_ctx = p.request.new_context()

        print(f"Ouverture index: {URL_ROOT}")
        page.goto(URL_ROOT, wait_until="domcontentloaded")

        # 1) Collecte initiale: sections + documents sur la page racine
        root_sections, root_docs = collect_links_on_page(page, URL_ROOT)
        print(f"Sections détectées (racine): {len(root_sections)} | Documents directs (racine): {len(root_docs)}")

        # 2) Préparer la liste de pages à explorer (sections)
        to_visit = list(root_sections)
        visited_pages = set()

        # 3) Télécharger d’abord les documents directs sur la racine
        ok = 0
        for doc_url in root_docs:
            filename = filename_from_url(doc_url)
            dest = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.exists(dest):
                continue

            mime, last_mod, clen = head_metadata(api_ctx, doc_url)
            print(f"Téléchargement (racine): {filename}")
            try:
                download_via_browser(page, doc_url, dest)
                size = os.path.getsize(dest)
                if size < SIZE_THRESHOLD:
                    os.remove(dest)
                    print(f"  -> Échec: trop petit ({size} o)")
                    log_entry(URL_ROOT, doc_url, filename, mime, size, last_mod, clen, "fail_too_small")
                else:
                    print(f"  -> OK ({size//1024} KB)")
                    log_entry(URL_ROOT, doc_url, filename, mime, size, last_mod, clen, "ok")
                    ok += 1
            except Exception as e:
                print(f"  -> Erreur: {e}")
                log_entry(URL_ROOT, doc_url, filename, mime, None, last_mod, clen, f"error:{e}")
            time.sleep(0.8)

        # 4) Explorer chaque section (large) et télécharger leurs documents
        while to_visit:
            section_url = to_visit.pop(0)
            if section_url in visited_pages:
                continue
            visited_pages.add(section_url)

            # Filtre pour rester dans le domaine et le périmètre
            parsed = urlparse(section_url)
            if "bcl.lu" not in parsed.netloc:
                continue

            print(f"Exploration section: {section_url}")
            try:
                page.goto(section_url, wait_until="domcontentloaded")
            except Exception as e:
                print(f"  -> Erreur navigation: {e}")
                continue

            sec_sections, sec_docs = collect_links_on_page(page, section_url)
            # Ajouter nouvelles sous-pages à visiter
            for s in sec_sections:
                if s not in visited_pages and s not in to_visit:
                    # On reste dans le périmètre documents_nationaux
                    if "/documents_nationaux/" in s:
                        to_visit.append(s)

            # Télécharger les documents trouvés dans cette section
            for doc_url in sec_docs:
                filename = filename_from_url(doc_url)
                dest = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.exists(dest):
                    continue

                mime, last_mod, clen = head_metadata(api_ctx, doc_url)
                print(f"Téléchargement (section): {filename}")
                try:
                    download_via_browser(page, doc_url, dest)
                    size = os.path.getsize(dest)
                    if size < SIZE_THRESHOLD:
                        os.remove(dest)
                        print(f"  -> Échec: trop petit ({size} o)")
                        log_entry(section_url, doc_url, filename, mime, size, last_mod, clen, "fail_too_small")
                    else:
                        print(f"  -> OK ({size//1024} KB)")
                        log_entry(section_url, doc_url, filename, mime, size, last_mod, clen, "ok")
                        ok += 1
                except Exception as e:
                    print(f"  -> Erreur: {e}")
                    log_entry(section_url, doc_url, filename, mime, None, last_mod, clen, f"error:{e}")
                time.sleep(0.8)

        print(f"\n--- Fin: {ok} fichier(s) téléchargé(s). ---")
        browser.close()


if __name__ == "__main__":
    crawl_and_download()
