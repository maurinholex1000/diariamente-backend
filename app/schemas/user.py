from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(BaseModel):
    username: str
    role: str = "patient"
    license_number: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    fcm_token: Optional[str] = None
    therapist_id: Optional[int] = None


class UserResponse(UserBase):
    id: int
    role: str
    firebase_uid: Optional[str] = None
    license_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"