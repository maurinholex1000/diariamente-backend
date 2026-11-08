from app.firebase_config import send_fcm_notification
from app.models.user import User
from app.models.diary_entry import DiaryEntry
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    async def send_crisis_alert(patient_id, entry_id, score, db: Session):
        try:
            patient = (
                db.query(User)
                .filter(User.id == patient_id)
                .first()
            )

            if not patient:
                return False

            therapist = None

            if patient.therapist_id:
                therapist = (
                    db.query(User)
                    .filter(User.id == patient.therapist_id)
                    .first()
                )

            notification_sent = False

            # Notificación al terapeuta.
            if therapist and therapist.fcm_token:
                response = send_fcm_notification(
                    device_token=therapist.fcm_token,
                    title="🚨 ALERTA DE CRISIS",
                    body=f"{patient.username} tiene Score {score:.0%}. Revisión inmediata.",
                    data={
                        "type": "crisis_alert",
                        "patient_id": str(patient_id),
                        "patient_name": patient.username,
                        "entry_id": str(entry_id),
                        "score": str(score),
                    },
                )

                if response:
                    notification_sent = True

            # Notificación al paciente.
            if patient.fcm_token:
                response = send_fcm_notification(
                    device_token=patient.fcm_token,
                    title="💙 Estamos acá para vos",
                    body="Detectamos que estás pasando por un momento difícil.",
                    data={
                        "type": "self_crisis_alert",
                        "entry_id": str(entry_id),
                    },
                )

                if response:
                    notification_sent = True

            entry = (
                db.query(DiaryEntry)
                .filter(DiaryEntry.id == entry_id)
                .first()
            )

            if entry:
                entry.crisis_notified = notification_sent
                db.commit()

            return notification_sent

        except Exception:
            db.rollback()
            logger.exception("Error enviando alerta de crisis")
            return False

    @staticmethod
    async def send_consent_request(therapist_id, patient_id, request_id, db: Session):
        try:
            patient = db.query(User).filter(User.id == patient_id).first()
            therapist = db.query(User).filter(User.id == therapist_id).first()

            if not patient or not patient.fcm_token or not therapist:
                return

            send_fcm_notification(
                device_token=patient.fcm_token,
                title="📋 Nueva Solicitud de Reporte",
                body=f"{therapist.username} solicitó acceso a tus pensamientos.",
                data={
                    "type": "consent_request",
                    "request_id": str(request_id),
                    "therapist_name": therapist.username,
                },
            )

        except Exception:
            logger.exception("Error enviando solicitud de consentimiento")

    @staticmethod
    async def send_report_ready(therapist_id, patient_id, report_id, db: Session):
        try:
            therapist = db.query(User).filter(User.id == therapist_id).first()
            patient = db.query(User).filter(User.id == patient_id).first()

            if not therapist or not therapist.fcm_token or not patient:
                return

            send_fcm_notification(
                device_token=therapist.fcm_token,
                title="📄 Reporte Listo",
                body=f"El reporte de {patient.username} está disponible.",
                data={
                    "type": "report_ready",
                    "report_id": str(report_id),
                    "patient_name": patient.username,
                },
            )

        except Exception:
            logger.exception("Error enviando notificación de reporte")