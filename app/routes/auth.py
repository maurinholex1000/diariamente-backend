from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.firebase_config import verify_token
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    firebase_uid = decoded_token.get("uid")
    token_email = decoded_token.get("email")

    if not firebase_uid or not token_email:
        raise HTTPException(
            status_code=401,
            detail="El token de Firebase no contiene una identidad válida",
        )

    if not decoded_token.get("email_verified", False):
        raise HTTPException(
            status_code=403,
            detail="Debés verificar tu email antes de vincular esta cuenta",
        )

    email = token_email.strip().lower()
    username = user_data.username.strip()

    if not username:
        raise HTTPException(
            status_code=422,
            detail="El nombre de usuario es obligatorio",
        )

    # Validar el rol solicitado.
    role = user_data.role.strip().lower()

    if role not in ("patient", "therapist"):
        raise HTTPException(
            status_code=422,
            detail="El rol seleccionado no es válido",
        )

    # La matrícula profesional será opcional.
    # Se podrá completar posteriormente desde el perfil del usuario.
    license_number = (
       user_data.license_number.strip()
       if user_data.license_number and user_data.license_number.strip()
       else None
    )

    if role == "patient":
        license_number = None

    # Si el UID ya existe, devolver el usuario.
    # Esto hace que el registro sea idempotente.
    existing_user = AuthService.get_user_by_firebase_uid(
        db,
        firebase_uid,
    )

    if existing_user:
        return existing_user

    # Si existe el email sin UID, vincular la cuenta de Firebase.
    existing_email = AuthService.get_user_by_email(db, email)

    if existing_email:
        if existing_email.firebase_uid is None:
            existing_email.firebase_uid = firebase_uid
            existing_email.username = username
            existing_email.role = role
            existing_email.license_number = license_number

            db.commit()
            db.refresh(existing_email)

            if role == "patient":
                AuthService.auto_assign_therapist(db, existing_email)

            return existing_email

        raise HTTPException(
            status_code=409,
            detail="El email ya está asociado a otra cuenta",
        )

    # Crear usuario conservando el rol y la matrícula.
    user = User(
        firebase_uid=firebase_uid,
        email=email,
        username=username,
        role=role,
        license_number=license_number,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # La asignación automática de terapeuta corresponde a pacientes.
    if role == "patient":
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
        user = AuthService.get_user_by_email(
            db,
            email.strip().lower(),
        )

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