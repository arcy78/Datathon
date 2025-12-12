import logging
import sys

def setup_logger(name="Application", log_file="app.log", level=logging.INFO):
    """
    Configure et retourne un logger.
    """
    # Création du logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Vérifie si des handlers existent déjà pour éviter les logs en double
    if not logger.handlers:
        # Format du log (Date - Nom - Niveau - Message)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Handler 1 : Écriture dans un fichier
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler 2 : Affichage dans la console (Optionnel mais recommandé)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger