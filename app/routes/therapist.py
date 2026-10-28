from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.therapist_patient import TherapistPatient
from app.models.consent_request import ConsentRequest
from app.models.diary_entry import DiaryEntry
from app.firebase_config import verify_token
from fastapi.responses import FileResponse

router = APIRouter(prefix="/therapist", tags=["Therapist"])


@router.get("/patients")
async def get_my_patients(
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

    relations = (
        db.query(TherapistPatient)
        .filter(TherapistPatient.therapist_id == therapist.id)
        .all()
    )
    patients = []
    for r in relations:
        patient = db.query(User).filter(User.id == r.patient_id).first()
        if patient:
            patients.append({
                "id": patient.id,
                "name": patient.username,
                "email": patient.email,
                "created_at": patient.created_at,
            })
    return patients


@router.post("/link-patient/{patient_email}")
async def link_patient(
    patient_email: str,
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

    patient = (
        db.query(User)
        .filter(User.email == patient_email, User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    existing = (
        db.query(TherapistPatient)
        .filter(
            TherapistPatient.therapist_id == therapist.id,
            TherapistPatient.patient_id == patient.id,
        )
        .first()
    )
    if existing:
        return {"message": "Ya estaba vinculado"}

    relation = TherapistPatient(therapist_id=therapist.id, patient_id=patient.id)
    db.add(relation)
    patient.therapist_id = therapist.id
    db.commit()

    return {"message": "Paciente vinculado", "patient_id": patient.id}


@router.get("/requests")
async def get_my_requests(
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

    requests = (
        db.query(ConsentRequest)
        .filter(ConsentRequest.therapist_id == therapist.id)
        .order_by(ConsentRequest.created_at.desc())
        .all()
    )
    result = []
    for r in requests:
        patient = db.query(User).filter(User.id == r.patient_id).first()
        result.append({
            "id": r.id,
            "patient_name": patient.username if patient else "Paciente",
            "patient_id": r.patient_id,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "status": r.status,
            "pdf_path": r.pdf_path,
            "created_at": r.created_at,
        })
    return result


@router.get("/download-report/{consent_id}")
async def download_report(
    consent_id: int,
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

    consent = (
        db.query(ConsentRequest)
        .filter(
            ConsentRequest.id == consent_id,
            ConsentRequest.therapist_id == therapist.id,
            ConsentRequest.status == "accepted",
        )
        .first()
    )
    if not consent or not consent.pdf_path or not os.path.exists(consent.pdf_path):
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    return FileResponse(
        consent.pdf_path,
        media_type="application/pdf",
        filename=f"reporte_{consent.patient_id}_{consent.id}.pdf",
    )


@router.get("/crisis-alerts")
async def get_crisis_alerts(
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

    patients = db.query(User).filter(User.therapist_id == therapist.id).all()
    patient_ids = [p.id for p in patients]
    if not patient_ids:
        return []

    entries = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.user_id.in_(patient_ids),
            DiaryEntry.flag_riesgo_suicida == True,  # noqa: E712
            DiaryEntry.crisis_notified == False,      # noqa: E712
        )
        .order_by(desc(DiaryEntry.created_at))
        .all()
    )

    result = []
    for entry in entries:
        patient = db.query(User).filter(User.id == entry.user_id).first()
        result.append({
            "id": entry.id,
            "patient_id": entry.user_id,
            "patient_name": patient.username if patient else "Paciente",
            "belief": entry.belief,
            "risk_score": entry.risk_score,
            "detected_emotion": entry.detected_emotion,
            "detected_distortion": entry.detected_distortion,
            "created_at": entry.created_at,
        })
    return result


@router.get("/crisis-alert/{entry_id}")
async def get_crisis_alert_detail(
    entry_id: int,
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

    entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    patient = db.query(User).filter(User.id == entry.user_id).first()
    if not patient or patient.therapist_id != therapist.id:
        raise HTTPException(status_code=403, detail="No tenés acceso")

    crisis_keywords = [
        "muerte", "morir", "matarme", "suicid", "terminar con todo",
        "no quiero vivir", "quiero morirme", "no despertar",
    ]
    keywords = [kw for kw in crisis_keywords if kw in entry.belief.lower()]

    return {
        "id": entry.id,
        "patient_id": entry.user_id,
        "patient_name": patient.username,
        "belief": entry.belief,
        "risk_score": entry.risk_score,
        "emotion": entry.detected_emotion or "No detectada",
        "distortion": entry.detected_distortion or "No detectada",
        "confidence": entry.confidence_score or 0,
        "keywords": keywords[:5],
        "created_at": entry.created_at,
    }


@router.post("/crisis-alert/{entry_id}/mark-attended")
async def mark_crisis_attended(
    entry_id: int,
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

    entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    patient = db.query(User).filter(User.id == entry.user_id).first()
    if not patient or patient.therapist_id != therapist.id:
        raise HTTPException(status_code=403, detail="No tenés acceso")

    entry.crisis_notified = True
    entry.crisis_attended_at = datetime.utcnow()
    entry.crisis_attended_by = therapist.id
    db.commit()
    return {"message": "Alerta marcada como atendida"}