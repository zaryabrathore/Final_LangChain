import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class DynamicSettings:
    def __init__ (self):
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        self.qdrant_host: str = os.getenv("QDRANT_HOST") or ""
        self.qdrant_api_key: str = os.getenv("QDRANT_API_KEY") or ""
        self.qdrant_collection: str = os.getenv("QDRANT_COLLECTION_NAME") or "pdf_rag_collection"
        self.github_token: str = os.getenv("GITHUB_TOKEN") or ""
        self.google_client_id: str = os.getenv("GOOGLE_CLIENT_ID") or ""
        self.google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET") or ""
        self.google_refresh_token: str = os.getenv("GOOGLE_REFRESH_TOKEN") or ""
        self.google_user_email: str = os.getenv("GOOGLE_USER_EMAIL") or "user@example.com"

    def update(self, new_settings: Dict[str, Any]):
        if "gemini_api_key" in new_settings:
            self.gemini_api_key = new_settings["gemini_api_key"]
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key
            os.environ["GOOGLE_API_KEY"] = self.gemini_api_key
        if "qdrant_host" in new_settings:
            self.qdrant_host = new_settings["qdrant_host"]
        if "qdrant_api_key" in new_settings:
            self.qdrant_api_key = new_settings["qdrant_api_key"]
        if "qdrant_collection" in new_settings:
            self.qdrant_collection = new_settings["qdrant_collection"]
        if "github_token" in new_settings:
            self.github_token = new_settings["github_token"]
            os.environ["GITHUB_TOKEN"] = self.github_token
        if "google_user_email" in new_settings:
            self.google_user_email = new_settings["google_user_email"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gemini_api_key_set": bool(self.gemini_api_key),
            "qdrant_host": self.qdrant_host,
            "qdrant_api_key_set": bool(self.qdrant_api_key),
            "qdrant_collection": self.qdrant_collection,
            "github_token_set": bool(self.github_token),
            "google_user_email": self.google_user_email,
            "google_client_id_set": bool(self.google_client_id)
        }

settings = DynamicSettings()
