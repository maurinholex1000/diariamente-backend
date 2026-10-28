from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.user_consent import UserConsent
from app.schemas.user_consent import UserConsentCreate, UserConsentResponse
from app.firebase_config import verify_token

router = APIRouter(prefix="/legal", tags=["Legal"])


@router.get("/consent", response_model=UserConsentResponse)
async def get_consent(
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    consent = db.query(UserConsent).filter(UserConsent.user_id == user.id).first()
    if not consent:
        return UserConsentResponse(
            id=0, user_id=user.id, version="1.0.0",
            accepted=False, accepted_at=None,
        )
    return consent


@router.post("/consent", response_model=UserConsentResponse)
async def accept_consent(
    data: UserConsentCreate,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    consent = db.query(UserConsent).filter(UserConsent.user_id == user.id).first()
    if consent:
        consent.version = data.version
        consent.accepted = True
        consent.accepted_at = datetime.utcnow()
    else:
        consent = UserConsent(
            user_id=user.id,
            version=data.version,
            accepted=True,
            accepted_at=datetime.utcnow(),
        )
        db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent