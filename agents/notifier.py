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
        if not self.user or not self.pwd: return
        
        relevant = [r for r in results if r['score'] > 0]
        if not relevant: return

        body = "RAPPORT DE VEILLE REGLEMENTAIRE\n\n"
        for doc in relevant:
            body += f"- {doc['source']} : {doc['file']} (Score: {doc['score']})\n"
            body += f"  Mots: {doc['matches']}\n  Lien: {doc['url']}\n\n"

        try:
            msg = MIMEText(body)
            msg['Subject'] = f"Alert Datathon: {len(relevant)} Documents Critiques"
            msg['From'] = self.user
            msg['To'] = self.user # S'envoie à soi-même pour test

            s = smtplib.SMTP(self.server, self.port)
            s.starttls()
            s.login(self.user, self.pwd)
            s.send_message(msg)
            s.quit()
            logger.info("Email de notification envoyé.")
        except Exception as e:
            logger.error(f"Erreur Email: {e}")