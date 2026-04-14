import os
import logging
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from datetime import datetime
from app.database import get_db
from app.services.ocr_service import get_ocr_service, OcrService
from app.services.ktp_parser import parse_ktp_text
from app.services.ai_ktp_parser import parse_ktp_with_ai
from app.models.ktp_ocr import KtpOcr
from app.schemas.ktp import KtpOcrDataResponse, KtpOcrErrorResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr/ktp", tags=["KTP OCR"])


@router.post(
    "",
    response_model=KtpOcrDataResponse,
    responses={
        400: {"model": KtpOcrErrorResponse, "description": "File tidak valid atau image tidak terbaca"},
        500: {"description": "Gagal menyimpan data KTP"},
    },
    summary="Upload gambar KTP dan ekstrak data",
    description="Upload gambar KTP Indonesia, ekstrak teks dengan PaddleOCR, parsing field KTP dengan AI (Qwen3:14b), dan simpan hasil ke database.",
    response_description="Data KTP hasil ekstraksi dan parsing",
)
async def ocr_ktp(
    image: UploadFile = File(..., description="File gambar KTP (jpeg/png/jpg/webp/bmp)"),
    db: AsyncSession = Depends(get_db),
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """
    Upload gambar KTP Indonesia, ekstrak teks dengan PaddleOCR, parsing field KTP dengan AI (Qwen3:14b), dan simpan hasil ke database.
    """
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp", "image/bmp"]
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File harus berupa gambar (jpeg/png/jpg/webp/bmp)")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"ktp_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{image.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    content = await image.read()
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    try:
        raw_text = ocr_service.extract_text_from_bytes(content)
    except Exception:
        raise HTTPException(status_code=400, detail="image tidak terbaca")

    # Parsing dengan AI, fallback ke regex jika gagal
    try:
        parsed = await parse_ktp_with_ai(raw_text)
    except ValueError:
        logger.warning("AI parsing gagal, fallback ke regex parser")
        parsed = parse_ktp_text(raw_text)

    now = datetime.utcnow()

    stmt = insert(KtpOcr).values(
        ktp_img=filename,
        raw_text=parsed["raw_text"],
        name=parsed["name"],
        nik=parsed["nik"],
        province=parsed["province"],
        birthdate=parsed["birthdate"],
        virgin=parsed["virgin"],
        status=parsed["status"],
        birthplace=parsed["birthplace"],
        city=parsed["city"],
        sub_district=parsed["sub_district"],
        village=parsed["village"],
        address=parsed["address"],
        rt=parsed["rt"],
        rw=parsed["rw"],
        religion=parsed["religion"],
        job=parsed["job"],
        citizenship=parsed["citizenship"],
        valid_until=parsed["valid_until"],
        created_at=now,
    ).returning(KtpOcr)
    result = await db.execute(stmt)
    await db.commit()
    ktp_row = result.fetchone()
    if not ktp_row:
        raise HTTPException(status_code=500, detail="Gagal menyimpan data KTP")
    ktp_obj = ktp_row[0]
    return {"data": ktp_obj}
