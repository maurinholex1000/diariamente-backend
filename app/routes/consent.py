from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
import os
import logging
from app.database import get_db
from app.models.user import User
from app.models.consent_request import ConsentRequest
from app.schemas.consent import (
    ConsentRequestCreate, ConsentRequestResponse, ConsentRespond,
)
from app.firebase_config import verify_token
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/consent", tags=["Consent"])
logger = logging.getLogger(__name__)


@router.post("/request")
async def create_request(
    request_data: ConsentRequestCreate,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    therapist = (
        db.query(User)
        .filter(User.firebase_uid == firebase_uid, User.role == "therapist")
        .first()
    )
    if not therapist:
        raise HTTPException(status_code=403, detail="Solo terapeutas")

    patient = db.query(User).filter(User.id == request_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    consent = ConsentRequest(
        therapist_id=therapist.id,
        patient_id=request_data.patient_id,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        status="pending",
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    await NotificationService.send_consent_request(
        therapist.id, patient.id, consent.id, db
    )
    return {"message": "Solicitud enviada", "request_id": consent.id}


@router.get("/requests", response_model=List[ConsentRequestResponse])
async def get_my_requests(
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    patient = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    requests = (
        db.query(ConsentRequest)
        .filter(ConsentRequest.patient_id == patient.id)
        .order_by(ConsentRequest.created_at.desc())
        .all()
    )
    result = []
    for r in requests:
        therapist = db.query(User).filter(User.id == r.therapist_id).first()
        result.append(
            ConsentRequestResponse(
                id=r.id,
                therapist_id=r.therapist_id,
                therapist_name=therapist.username if therapist else "Terapeuta",
                patient_id=r.patient_id,
                start_date=r.start_date,
                end_date=r.end_date,
                status=r.status,
                created_at=r.created_at,
            )
        )
    return result


@router.post("/respond/{request_id}")
async def respond_to_request(
    request_id: int,
    response: ConsentRespond,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    patient = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    consent = (
        db.query(ConsentRequest)
        .filter(
            ConsentRequest.id == request_id,
            ConsentRequest.patient_id == patient.id,
        )
        .first()
    )
    if not consent:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    new_status = "accepted" if response.accept else "rejected"
    consent.status = new_status

    if response.accept:
        report_data = ReportService.generate_report(
            consent.patient_id, consent.start_date, consent.end_date, db
        )
        consent.report_data = json.dumps(report_data, ensure_ascii=False)

        try:
            pdf_bytes = ReportService.generate_pdf(report_data)
            os.makedirs("reports", exist_ok=True)
            pdf_path = (
                f"reports/report_{consent.id}_"
                f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            consent.pdf_path = pdf_path
            consent.report_generated_at = datetime.utcnow()
            await NotificationService.send_report_ready(
                consent.therapist_id, consent.patient_id, consent.id, db
            )
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")

    db.commit()
    return {"status": new_status}