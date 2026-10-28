from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserConsentCreate(BaseModel):
    version: str
    accepted_at: Optional[datetime] = None


class UserConsentResponse(BaseModel):
    id: int
    user_id: int
    version: str
    accepted: bool
    accepted_at: Optional[datetime]

    class Config:
        from_attributes = True