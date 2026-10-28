from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DiaryEntryBase(BaseModel):
    antecedent: Optional[str] = None
    belief: str
    consequence: Optional[str] = None
    user_emotion: Optional[str] = None


class DiaryEntryCreate(DiaryEntryBase):
    detected_emotion: Optional[str] = None
    detected_distortion: Optional[str] = None
    confidence_score: Optional[float] = None


class DiaryEntryResponse(DiaryEntryBase):
    id: int
    detected_emotion: Optional[str] = None
    detected_distortion: Optional[str] = None
    confidence_score: Optional[float] = None
    risk_score: Optional[float] = None
    flag_riesgo_suicida: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True