from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Optional


class OcrResultBase(BaseModel):
    filename: str


class OcrResultCreate(OcrResultBase):
    pass


class OcrResultResponse(OcrResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    extracted_text: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class OcrResultList(BaseModel):
    items: list[OcrResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
