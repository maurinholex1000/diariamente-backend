from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://diariamente_user:diariamente123@localhost/diariamente_db"
    firebase_credentials: str = "firebase-service-account.json"
    app_name: str = "DIAriaMENTE API"
    app_version: str = "3.0.0"
    debug: bool = True
    gcp_project_id: Optional[str] = None
    kms_key_ring: Optional[str] = None
    kms_crypto_key: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()