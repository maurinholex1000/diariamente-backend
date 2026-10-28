from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.firebase_config import verify_token, send_fcm_notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class FCMTokenRequest(BaseModel):
    token: str


@router.post("/register-token")
async def register_fcm_token(
    request: FCMTokenRequest,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.fcm_token = request.token
    db.commit()
    return {"message": "Token registrado"}


@router.post("/test")
async def test_notification(
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user or not user.fcm_token:
        raise HTTPException(status_code=404, detail="No hay token FCM")

    result = send_fcm_notification(
        device_token=user.fcm_token,
        title="🔔 Prueba",
        body="¡FCM funciona!",
        data={"type": "test"},
    )
    if not result:
        raise HTTPException(status_code=500, detail="Error enviando")
    return {"message": "Enviada", "fcm_id": result}