from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from typing import List
import logging

from app.database import get_db
from app.models.user import User
from app.models.diary_entry import DiaryEntry
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryResponse
from app.firebase_config import verify_token
from app.services.risk_classifier_hybrid import HybridRiskClassifier
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/diary", tags=["Diary"])
logger = logging.getLogger(__name__)

_risk_classifier = None


def get_risk_classifier():
    global _risk_classifier

    if _risk_classifier is None:
        _risk_classifier = HybridRiskClassifier()

    return _risk_classifier


@router.post("/entries", response_model=DiaryEntryResponse)
async def create_entry(
    entry_data: DiaryEntryCreate,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")

    user = (
        db.query(User)
        .filter(User.firebase_uid == firebase_uid)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    # 1. Si el cliente envía un identificador, buscamos si ya existe.
    # La búsqueda siempre está limitada al usuario autenticado.
    if entry_data.client_entry_id:
        existing_entry = (
            db.query(DiaryEntry)
            .filter(
                DiaryEntry.user_id == user.id,
                DiaryEntry.client_entry_id == entry_data.client_entry_id,
            )
            .first()
        )

        if existing_entry:
            logger.info(
                "Pensamiento duplicado evitado. Usuario=%s, client_entry_id=%s",
                user.id,
                entry_data.client_entry_id,
            )
            return existing_entry

    # 2. Creamos el pensamiento.
    db_entry = DiaryEntry(
        user_id=user.id,
        client_entry_id=entry_data.client_entry_id,
        antecedent=entry_data.antecedent,
        belief=entry_data.belief,
        consequence=entry_data.consequence,
        user_emotion=entry_data.user_emotion,
        detected_emotion=entry_data.detected_emotion,
        detected_distortion=entry_data.detected_distortion,
        confidence_score=entry_data.confidence_score,
    )

    db.add(db_entry)

    try:
        db.commit()
        db.refresh(db_entry)

    except IntegrityError:
        db.rollback()

        # 3. Protección adicional ante dos solicitudes simultáneas.
        if entry_data.client_entry_id:
            existing_entry = (
                db.query(DiaryEntry)
                .filter(
                    DiaryEntry.user_id == user.id,
                    DiaryEntry.client_entry_id == entry_data.client_entry_id,
                )
                .first()
            )

            if existing_entry:
                logger.info(
                    "Solicitud simultánea duplicada evitada. Usuario=%s, client_entry_id=%s",
                    user.id,
                    entry_data.client_entry_id,
                )
                return existing_entry

        logger.exception("Error de integridad al guardar pensamiento")
        raise HTTPException(
            status_code=409,
            detail="No se pudo guardar el pensamiento por un conflicto de datos",
        )

    # 4. El análisis de riesgo se realiza únicamente al crear un pensamiento nuevo.
    if entry_data.belief:
        try:
            risk_classifier = get_risk_classifier()

            risk_score, flag, reason = (
                risk_classifier.calculate_risk_score(entry_data.belief)
            )

            db_entry.risk_score = risk_score
            db_entry.flag_riesgo_suicida = flag

            db.commit()
            db.refresh(db_entry)

            if flag:
                logger.warning(
                    "🚨 CRISIS - %s: %s",
                    user.username,
                    reason,
                )

                await NotificationService.send_crisis_alert(
                    user.id,
                    db_entry.id,
                    risk_score,
                    db,
                )

                db.refresh(db_entry)

        except Exception:
            db.rollback()
            logger.exception("Error en análisis de riesgo")

            # Recuperamos el pensamiento ya guardado.
            db.refresh(db_entry)

    return db_entry


@router.get("/entries", response_model=List[DiaryEntryResponse])
async def get_entries(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")

    user = (
        db.query(User)
        .filter(User.firebase_uid == firebase_uid)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    entries = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == user.id)
        .order_by(desc(DiaryEntry.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return entries