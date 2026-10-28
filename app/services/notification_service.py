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
            patient = db.query(User).filter(User.id == patient_id).first()
            if not patient:
                return

            therapist = db.query(User).filter(User.id == patient.therapist_id).first()
            if therapist and therapist.fcm_token:
                send_fcm_notification(
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

            if patient.fcm_token:
                send_fcm_notification(
                    device_token=patient.fcm_token,
                    title="💙 Estamos acá para vos",
                    body="Detectamos que estás pasando por un momento difícil.",
                    data={"type": "self_crisis_alert", "entry_id": str(entry_id)},
                )

            entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
            if entry:
                entry.crisis_notified = True
                db.commit()
        except Exception as e:
            logger.error(f"Error alerta crisis: {e}")

    @staticmethod
    async def send_consent_request(therapist_id, patient_id, request_id, db: Session):
        try:
            patient = db.query(User).filter(User.id == patient_id).first()
            therapist = db.query(User).filter(User.id == therapist_id).first()
            if not patient or not patient.fcm_token:
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
        except Exception as e:
            logger.error(f"Error consent request: {e}")

    @staticmethod
    async def send_report_ready(therapist_id, patient_id, report_id, db: Session):
        try:
            therapist = db.query(User).filter(User.id == therapist_id).first()
            patient = db.query(User).filter(User.id == patient_id).first()
            if not therapist or not therapist.fcm_token:
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
        except Exception as e:
            logger.error(f"Error report ready: {e}")