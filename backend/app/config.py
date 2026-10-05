import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class DynamicSettings:
    def __init__(self):
        self._custom_settings: Dict[str, Any] = {}

    def _reload_env(self):
        load_dotenv(override=True)

    @property
    def gemini_api_key(self) -> str:
        return self._custom_settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

    @property
    def qdrant_host(self) -> str:
        return self._custom_settings.get("qdrant_host") or os.getenv("QDRANT_HOST") or ""

    @property
    def qdrant_api_key(self) -> str:
        return self._custom_settings.get("qdrant_api_key") or os.getenv("QDRANT_API_KEY") or ""

    @property
    def qdrant_collection(self) -> str:
        return self._custom_settings.get("qdrant_collection") or os.getenv("QDRANT_COLLECTION_NAME") or "pdf_rag_collection"

    @property
    def github_token(self) -> str:
        return self._custom_settings.get("github_token") or os.getenv("GITHUB_TOKEN") or ""

    @property
    def google_client_id(self) -> str:
        load_dotenv(override=True)
        return self._custom_settings.get("google_client_id") or os.getenv("GOOGLE_CLIENT_ID") or ""

    @property
    def google_client_secret(self) -> str:
        load_dotenv(override=True)
        return self._custom_settings.get("google_client_secret") or os.getenv("GOOGLE_CLIENT_SECRET") or ""

    @property
    def google_refresh_token(self) -> str:
        load_dotenv(override=True)
        return self._custom_settings.get("google_refresh_token") or os.getenv("GOOGLE_REFRESH_TOKEN") or ""

    @property
    def google_user_email(self) -> str:
        return self._custom_settings.get("google_user_email") or os.getenv("GOOGLE_USER_EMAIL") or "user@example.com"

    @property
    def gmail_app_password(self) -> str:
        load_dotenv(override=True)
        return self._custom_settings.get("gmail_app_password") or os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_PASSWORD") or ""

    def update(self, new_settings: Dict[str, Any]):
        for key, val in new_settings.items():
            if val is not None:
                self._custom_settings[key] = val
                os.environ[key.upper()] = str(val)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gemini_api_key_set": bool(self.gemini_api_key),
            "qdrant_host": self.qdrant_host,
            "qdrant_api_key_set": bool(self.qdrant_api_key),
            "qdrant_collection": self.qdrant_collection,
            "github_token_set": bool(self.github_token),
            "google_user_email": self.google_user_email,
            "google_client_id_set": bool(self.google_client_id),
            "gmail_app_password_set": bool(self.gmail_app_password)
        }

settings = DynamicSettings()
