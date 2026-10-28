from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.firebase_config import verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = AuthService.get_user_by_firebase_uid(db, user_data.firebase_uid)
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya está registrado")

    existing_email = AuthService.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user = AuthService.create_user(db, user_data)

    if user.role == "patient":
        AuthService.auto_assign_therapist(db, user)

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    user = AuthService.get_user_by_firebase_uid(db, firebase_uid)
    if not user and email:
        user = AuthService.get_user_by_email(db, email)
        if user and not user.firebase_uid:
            user.firebase_uid = firebase_uid
            db.commit()
            db.refresh(user)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user