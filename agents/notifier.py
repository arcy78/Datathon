# agents/notifier.py
import smtplib
from email.mime.text import MIMEText
import os
from utils.logger import setup_logger

logger = setup_logger()

class NotificationAgent:
    def __init__(self):
        self.user = os.getenv("EMAIL_USER")
        self.pwd = os.getenv("EMAIL_PASSWORD")
        self.server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", 587))

    def send_report(self, results):
        if not self.user or not self.pwd: 
            logger.warning("Email non configuré, pas de notif.")
            return
        
        body = "RAPPORT VEILLE NREL API\n\n"
        for item in results:
            body += f"Composant: {item['file']}\nMatchs: {item['matches']}\nScore: {item['score']}\n\n"

        try:
            msg = MIMEText(body)
            msg['Subject'] = f"Alerte BCL API: {len(results)} Composants Détectés"
            msg['From'] = self.user
            msg['To'] = self.user
            
            s = smtplib.SMTP(self.server, self.port)
            s.starttls()
            s.login(self.user, self.pwd)
            s.send_message(msg)
            s.quit()
        except Exception as e:
            logger.error(f"Erreur Mail: {e}")