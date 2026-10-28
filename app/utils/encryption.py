import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

try:
    from google.cloud import kms
    KMS_AVAILABLE = True
except ImportError:
    KMS_AVAILABLE = False
    logger.warning("google-cloud-kms no instalado.")


class EncryptionService:
    def __init__(self):
        self.enabled = (
            KMS_AVAILABLE
            and settings.gcp_project_id
            and settings.kms_key_ring
            and settings.kms_crypto_key
        )
        if self.enabled:
            self.client = kms.KeyManagementServiceClient()
            self.key_name = self.client.crypto_key_path(
                settings.gcp_project_id, "global",
                settings.kms_key_ring, settings.kms_crypto_key,
            )
            logger.info("✅ Cloud KMS inicializado")

    def encrypt(self, plaintext: str) -> Optional[bytes]:
        if not self.enabled:
            return plaintext.encode("utf-8")
        try:
            response = self.client.encrypt(
                request={"name": self.key_name, "plaintext": plaintext.encode("utf-8")}
            )
            return response.ciphertext
        except Exception as e:
            logger.error(f"Error encriptando: {e}")
            return None

    def decrypt(self, ciphertext: bytes) -> Optional[str]:
        if not self.enabled:
            return ciphertext.decode("utf-8")
        try:
            response = self.client.decrypt(
                request={"name": self.key_name, "ciphertext": ciphertext}
            )
            return response.plaintext.decode("utf-8")
        except Exception as e:
            logger.error(f"Error desencriptando: {e}")
            return None


encryption_service = EncryptionService()