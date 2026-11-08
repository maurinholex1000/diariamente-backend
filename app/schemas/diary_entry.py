from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DiaryEntryBase(BaseModel):
    antecedent: Optional[str] = None
    belief: str
    consequence: Optional[str] = None
    user_emotion: Optional[str] = None


class DiaryEntryCreate(DiaryEntryBase):
    client_entry_id: Optional[str] = Field(default=None, max_length=36)

    detected_emotion: Optional[str] = None
    detected_distortion: Optional[str] = None
    confidence_score: Optional[float] = None


class DiaryEntryResponse(DiaryEntryBase):
    id: int
    client_entry_id: Optional[str] = None

    detected_emotion: Optional[str] = None
    detected_distortion: Optional[str] = None
    confidence_score: Optional[float] = None

    risk_score: Optional[float] = None
    flag_riesgo_suicida: Optional[bool] = None

    crisis_notified: Optional[bool] = None
    crisis_attended_at: Optional[datetime] = None
    crisis_attended_by: Optional[int] = None

    created_at: datetime

    class Config:
        from_attributes = True