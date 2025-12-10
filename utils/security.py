import re
import hashlib

class SecurityManager:
    """Gère la validation des entrées et la sécurité des données."""

    @staticmethod
    def validate_url(url: str, allowed_domain: str) -> bool:
        """Empêche les attaques SSRF en vérifiant le domaine."""
        try:
            pattern = r"https?://(www\.)?([\w\-\.]+)"
            match = re.search(pattern, url)
            if match:
                domain = match.group(2)
                return allowed_domain in domain
            return False
        except Exception:
            return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Empêche le Path Traversal."""
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    @staticmethod
    def check_password(input_password: str, stored_hash: str) -> bool:
        """Vérification sécurisée du mot de passe."""
        input_hash = hashlib.sha256(input_password.encode()).hexdigest()
        return input_hash == stored_hash