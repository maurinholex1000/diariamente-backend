from pydantic import BaseModel
from datetime import datetime


class ConsentRequestCreate(BaseModel):
    patient_id: int
    start_date: datetime
    end_date: datetime


class ConsentRequestResponse(BaseModel):
    id: int
    therapist_id: int
    therapist_name: str
    patient_id: int
    start_date: datetime
    end_date: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConsentRespond(BaseModel):
    accept: bool