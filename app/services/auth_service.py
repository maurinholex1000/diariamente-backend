from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate


class AuthService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        db_user = User(
            firebase_uid=user_data.firebase_uid,
            email=user_data.email,
            username=user_data.username,
            role=user_data.role,
            license_number=user_data.license_number,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_firebase_uid(db: Session, firebase_uid: str):
        return db.query(User).filter(User.firebase_uid == firebase_uid).first()

    @staticmethod
    def auto_assign_therapist(db: Session, patient: User):
        therapist = (
            db.query(User)
            .filter(User.role == "therapist", User.is_active == True)  # noqa: E712
            .first()
        )
        if therapist:
            patient.therapist_id = therapist.id
            db.commit()