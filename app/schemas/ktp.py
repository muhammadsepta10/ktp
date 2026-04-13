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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "raw_text": "PROVINSI DKI JAKARTA...",
                "nik": "3171234567890001",
                "name": "BUDI SANTOSO",
                "city": "JAKARTA PUSAT",
                "province": "DKI JAKARTA",
                "sub_district": "BENDUNGAN HILIR",
                "village": "PEJOMPONGAN",
                "rt": "001",
                "rw": "002",
                "address": "JL. SUDIRMAN NO. 1",
                "virgin": "LAKI-LAKI",
                "birthplace": "JAKARTA",
                "birthdate": "01-01-1990",
                "religion": "ISLAM",
                "status": "BELUM KAWIN",
                "job": "KARYAWAN SWASTA",
                "citizenship": "WNI",
                "valid_until": "SEUMUR HIDUP",
                "created_at": "2026-04-13T10:30:00"
            }
        }
    )

class KtpOcrDataResponse(BaseModel):
    data: KtpOcrResponse
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "raw_text": "PROVINSI DKI JAKARTA...",
                    "nik": "3171234567890001",
                    "name": "BUDI SANTOSO",
                    "city": "JAKARTA PUSAT",
                    "province": "DKI JAKARTA",
                    "sub_district": "BENDUNGAN HILIR",
                    "village": "PEJOMPONGAN",
                    "rt": "001",
                    "rw": "002",
                    "address": "JL. SUDIRMAN NO. 1",
                    "virgin": "LAKI-LAKI",
                    "birthplace": "JAKARTA",
                    "birthdate": "01-01-1990",
                    "religion": "ISLAM",
                    "status": "BELUM KAWIN",
                    "job": "KARYAWAN SWASTA",
                    "citizenship": "WNI",
                    "valid_until": "SEUMUR HIDUP",
                    "created_at": "2026-04-13T10:30:00"
                }
            }
        }
    )

class KtpOcrErrorResponse(BaseModel):
    error: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "image tidak terbaca"
            }
        }
    )

class KtpOcrDataResponse(BaseModel):
    data: KtpOcrResponse

class KtpOcrErrorResponse(BaseModel):
    error: str
