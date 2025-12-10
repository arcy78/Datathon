# Configuration des Sources Cibles
# Scalabilité : Ajoutez simplement un dictionnaire ici pour ajouter une banque.

SOURCES_CONFIG = [
    {
        "name": "Banque Centrale du Luxembourg (BCL)",
        "type": "json",  # Utilise l'API JSON (Plus fiable)
        "url": "https://www.bcl.lu/fr/reglementation/circulaires/_jcr_content.listing.generate.json",
        "base_url_for_files": "https://www.bcl.lu", # Préfixe pour les liens relatifs
        "domain": "bcl.lu", # Sécurité : Whitelist de domaine
        "limit": 3 # Nombre max de documents à analyser
    },
    {
        "name": "European Central Bank (ECB)",
        "type": "html", # Fallback sur le scraping classique
        "url": "https://www.ecb.europa.eu/home/html/index.en.html",
        "domain": "ecb.europa.eu",
        "limit": 2
    }
]

# Seuils d'alerte
ALERT_THRESHOLD = 1 # Nombre de mots-clés min pour déclencher une notif