
import firebase_admin
from firebase_admin import credentials, auth, messaging
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

import logging
import os
import json

logger = logging.getLogger(__name__)


def initialize_firebase():
    """Inicializa Firebase usando credenciales locales o variables de entorno."""

    if firebase_admin._apps:
        return

    # Opción 1: credenciales JSON configuradas en el hosting.
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise RuntimeError(
                "Las credenciales FIREBASE_SERVICE_ACCOUNT_JSON "
                "no tienen un formato válido."
            ) from e

    # Opción 2: archivo local de credenciales.
    else:
        cred_path = settings.firebase_credentials

        if not os.path.isfile(cred_path):
            raise RuntimeError(
                f"No se encontró el archivo '{cred_path}'. "
                "Configurá FIREBASE_SERVICE_ACCOUNT_JSON "
                "o verificá la ruta de las credenciales locales."
            )

        cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred)

    logger.info("Firebase Admin SDK inicializado correctamente")


initialize_firebase()


security = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado"
        )

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    except Exception as e:
        logger.error(f"Error verificando token: {e}")

        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )


def send_fcm_notification(
    device_token: str,
    title: str,
    body: str,
    data: dict = None
):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data={
                k: str(v)
                for k, v in (data or {}).items()
            },
            token=device_token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    channel_id="diariamente-crisis",
                    priority="max",
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        badge=1
                    ),
                ),
            ),
        )

        response = messaging.send(message)

        logger.info(f"Notificación FCM enviada: {response}")

        return response

    except Exception as e:
        logger.error(f"Error enviando notificación FCM: {e}")
        return None
