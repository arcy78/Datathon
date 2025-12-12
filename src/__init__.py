# src/__init__.py (Optionnel, mais plus propre pour les importations)

# Expose les fonctions clés directement sous 'from src import ...'
from .bcl_scrapper import crawl_and_download
from .doc_translator import dispatch_file_for_translation, MODEL_MAP
from .security_config import ensure_secure_dirs