# agent_ai4_email.py
import streamlit as st
import pandas as pd
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ==========================================
# CONFIGURATION AUTOMATIQUE
# ==========================================
CSV_DESTINATAIRES = "Destinataire_CSV.csv"
DEFAULT_SENDER = "mamarie.kouam@gmail.com"
# Récupération du mot de passe (Env Var ou Hardcodé comme demandé)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "hcny hyun fnxg gxmt")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ==========================================
# 1. FONCTIONS UTILITAIRES
# ==========================================

def get_sender_email():
    """Récupère l'email du logger (session) ou le défaut."""
    user_email = st.session_state.get('user_email')
    if user_email and user_email != "DEFAULT_USER" and "@" in user_email:
        return user_email
    return DEFAULT_SENDER

def get_recipients_list():
    """Lit le fichier CSV et retourne une liste d'emails."""
    if not os.path.exists(CSV_DESTINATAIRES):
        return []
    try:
        # On essaie de lire avec séparateur point-virgule ou virgule
        df = pd.read_csv(CSV_DESTINATAIRES, sep=None, engine='python')
        # On suppose que les emails sont dans la 1ère colonne
        return df.iloc[:, 0].dropna().unique().tolist()
    except Exception as e:
        st.error(f"Erreur lecture CSV : {e}")
        return []

def generate_html_body(df):
    """Génère le corps HTML (inchangé)."""
    has_translation = 'Traduction du Contexte' in df.columns
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #2E86C1;">📊 Rapport de Veille Documentaire</h2>
        <p>Bonjour,</p>
        <p>Voici les éléments détectés par l'Agent IA :</p>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f8f9fa;">
                <th style="padding: 10px;">Fichier</th>
                <th style="padding: 10px;">Mot-clé</th>
                <th style="padding: 10px;">Résultat</th>
            </tr>
    """
    for _, row in df.iterrows():
        content = row['Traduction du Contexte'] if has_translation else row.get('Extrait du Contexte', '-')
        html += f"""
            <tr>
                <td style="padding: 8px;">{row['Fichier']}</td>
                <td style="padding: 8px; font-weight: bold;">{row['Mot-clé Cible']}</td>
                <td style="padding: 8px;">{content}</td>
            </tr>
        """
    html += "</table></body></html>"
    return html

def send_email_single(df, sender, password, receiver):
    """Envoie un mail unique."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"🔔 Alerte Veille ({len(df)} docs) - {pd.Timestamp.now().strftime('%d/%m/%Y')}"

        body = generate_html_body(df)
        msg.attach(MIMEText(body, 'html'))

        csv_data = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(csv_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= Rapport_Veille.csv")
        msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True, "OK"
    except Exception as e:
        return False, str(e)

# ==========================================
# 2. INTERFACE STREAMLIT
# ==========================================

def run_email_agent_interface():
    st.title("📧 Agent AI 4 : Notificateur de Masse")
    
    # --- A. Configuration Automatique (Affichage Read-Only) ---
    sender = get_sender_email()
    recipients = get_recipients_list()
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.success(f"📤 Expéditeur :\n{sender}")
        st.info(f"🔑 Password SMTP :\nConfiguré (env var)")
        
        st.markdown("---")
        st.header("👥 Destinataires (CSV)")
        if recipients:
            st.write(f"**{len(recipients)} contacts trouvés**")
            with st.expander("Voir la liste"):
                st.write(recipients)
        else:
            st.error(f"❌ Fichier '{CSV_DESTINATAIRES}' introuvable ou vide.")

    # --- B. Récupération Données ---
    if 'final_report' in st.session_state:
        df_to_send = st.session_state['final_report']
        st.success("✅ Rapport traduit récupéré.")
    elif 'analysis_results' in st.session_state:
        df_to_send = st.session_state['analysis_results']
        df_to_send = df_to_send[df_to_send['Statut'] == 'Trouvé']
        st.info("ℹ️ Rapport brut récupéré.")
    else:
        st.warning("⛔ Aucune donnée à envoyer.")
        return

    if df_to_send.empty:
        st.warning("Rapport vide.")
        return

    # --- C. Action d'Envoi ---
    st.subheader(f"Campagne d'envoi vers {len(recipients)} destinataires")
    
    if st.button("Lancer la diffusion 🚀", type="primary", disabled=(len(recipients)==0)):
        progress_bar = st.progress(0)
        status_text = st.empty()
        success_count = 0
        
        for i, receiver in enumerate(recipients):
            status_text.text(f"Envoi en cours vers {receiver}...")
            
            # Envoi
            ok, msg = send_email_single(df_to_send, sender, SMTP_PASSWORD, receiver)
            
            if ok:
                success_count += 1
            else:
                st.error(f"Échec vers {receiver}: {msg}")
            
            # Petite pause pour ne pas spammer le serveur SMTP trop vite
            time.sleep(1) 
            progress_bar.progress((i + 1) / len(recipients))
            
        status_text.text("Diffusion terminée !")
        st.balloons()
        st.success(f"✅ Campagne terminée : {success_count}/{len(recipients)} emails envoyés avec succès.")

if __name__ == "__main__":
    run_email_agent_interface()