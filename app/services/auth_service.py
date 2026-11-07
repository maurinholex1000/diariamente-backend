from sqlalchemy.orm import Session
from app.models.user import User


class AuthService:

    @staticmethod
    def create_user(
        db: Session,
        *,
        firebase_uid: str,
        email: str,
        username: str,
        role: str = "patient",
    ) -> User:
        db_user = User(
            firebase_uid=firebase_uid,
            email=email,
            username=username,
            role=role,
            license_number=None,
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
            .filter(
                User.role == "therapist",
                User.is_active == True,  # noqa: E712
            )
            .first()
        )

        if therapist:
            patient.therapist_id = therapist.id
            db.commit()
            db.refresh(patient)