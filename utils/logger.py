import logging

def setup_logger(name='app_logger', log_file='app.log'):
    """
    Fonction de réparation pour créer un logger simple.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Évite de créer des doublons de logs
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger