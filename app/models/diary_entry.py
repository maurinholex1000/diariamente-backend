from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.database import Base


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "client_entry_id",
            name="uq_diary_entries_user_client_entry",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Identificador generado por el dispositivo para evitar duplicados.
    # Es nullable para mantener compatibilidad con pensamientos anteriores.
    client_entry_id = Column(String(36), nullable=True)

    antecedent = Column(Text)
    belief = Column(Text, nullable=False)
    consequence = Column(Text)
    user_emotion = Column(String(50))

    detected_emotion = Column(String(50))
    detected_distortion = Column(String(100))
    confidence_score = Column(Float)

    risk_score = Column(Float, default=0.0)
    flag_riesgo_suicida = Column(Boolean, default=False)
    crisis_notified = Column(Boolean, default=False)
    crisis_attended_at = Column(DateTime, nullable=True)
    crisis_attended_by = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())