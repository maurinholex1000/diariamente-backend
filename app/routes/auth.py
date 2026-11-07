from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.firebase_config import verify_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    # La identidad proviene exclusivamente del token validado por Firebase.
    firebase_uid = decoded_token.get("uid")
    token_email = decoded_token.get("email")

    if not firebase_uid or not token_email:
        raise HTTPException(
            status_code=401,
            detail="El token de Firebase no contiene una identidad válida",
        )

    # Verificar que el correo de Firebase esté confirmado.
    if not decoded_token.get("email_verified", False):
        raise HTTPException(
            status_code=403,
            detail="Debés verificar tu email antes de vincular esta cuenta",
    )

    email = token_email.strip().lower()

    # Evitar registrar dos veces el mismo UID.
    existing_user = AuthService.get_user_by_firebase_uid(
        db,
        firebase_uid,
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="El usuario ya está registrado",
        )

    # Si ya existe una cuenta con ese email y todavía no tiene UID,
    # vinculamos la identidad autenticada de Firebase.
    existing_email = AuthService.get_user_by_email(db, email)

    if existing_email:
        if existing_email.firebase_uid is None:
            existing_email.firebase_uid = firebase_uid
            db.commit()
            db.refresh(existing_email)
            return existing_email

        raise HTTPException(
            status_code=409,
            detail="El email ya está asociado a otra cuenta",
        )

    # Los registros públicos siempre se crean como pacientes.
    # Nunca tomamos el rol enviado por el frontend.
    user = AuthService.create_user(
        db,
        firebase_uid=firebase_uid,
        email=email,
        username=user_data.username.strip(),
        role="patient",
    )

    AuthService.auto_assign_therapist(db, user)

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    if not firebase_uid:
        raise HTTPException(
            status_code=401,
            detail="Identidad de Firebase inválida",
        )

    user = AuthService.get_user_by_firebase_uid(db, firebase_uid)

    if not user and email:
        user = AuthService.get_user_by_email(db, email.strip().lower())

        if user and not user.firebase_uid:
            user.firebase_uid = firebase_uid
            db.commit()
            db.refresh(user)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="La cuenta está desactivada",
        )

    return user