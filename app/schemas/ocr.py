from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Optional


class OcrResultBase(BaseModel):
    filename: str


class OcrResultCreate(OcrResultBase):
    pass



class OcrResultResponse(OcrResultBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "filename": "document.png",
                "extracted_text": "Teks yang diekstrak dari gambar",
                "status": "completed",
                "created_at": "2026-04-13T10:30:00",
                "updated_at": "2026-04-13T10:30:05"
            }
        }
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "filename": "document.png",
                        "extracted_text": "Teks yang diekstrak dari gambar",
                        "status": "completed",
                        "created_at": "2026-04-13T10:30:00",
                        "updated_at": "2026-04-13T10:30:05"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10,
                "total_pages": 1
            }
        }
    )


class OcrResultList(BaseModel):
    items: list[OcrResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
