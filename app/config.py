
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    firebase_credentials: str = "firebase-service-account.json"

    app_name: str = "DIAriaMENTE API"
    app_version: str = "3.0.0"
    debug: bool = False

    gcp_project_id: Optional[str] = None
    kms_key_ring: Optional[str] = None
    kms_crypto_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
