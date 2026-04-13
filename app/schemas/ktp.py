from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class KtpOcrResponse(BaseModel):
    raw_text: str
    nik: str
    name: str
    city: str
    province: str
    sub_district: str
    village: str
    rt: str
    rw: str
    address: str
    virgin: str
    birthplace: str
    birthdate: str
    religion: str
    status: str
    job: str
    citizenship: str
    valid_until: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KtpOcrDataResponse(BaseModel):
    data: KtpOcrResponse

class KtpOcrErrorResponse(BaseModel):
    error: str
