import logging
import os
import re
import uuid
import aiofiles
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi import UploadFile, File
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.ocr_result import OcrResult
from app.schemas.ocr import OcrResultResponse, OcrResultList
from app.services.ocr_service import get_ocr_service, OcrService
from app.config import settings
from app.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"], dependencies=[Depends(verify_api_key)])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and special characters."""
    if not filename:
        return "upload.png"
    # Extract just the basename, stripping any directory components
    name = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dots, hyphens, underscores
    name = re.sub(r"[^\w.\-]", "_", name)
    return name or "upload.png"


def _validate_extension(filename: str) -> str:
    """Validate and return a safe file extension."""
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".png"
    return ext


async def save_upload_file(upload_file: UploadFile) -> tuple[str, bytes]:
    """Save uploaded file and return path and content."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate unique filename with safe extension
    ext = _validate_extension(upload_file.filename or "")
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    # Read content with size limit
    content = await upload_file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    return filename, content


@router.post(
    "",
    response_model=OcrResultResponse,
    status_code=201,
    summary="Upload image untuk OCR",
    description="Upload file gambar untuk diekstrak teksnya menggunakan PaddleOCR. File yang didukung: JPEG, PNG, GIF, WebP, BMP.",
    response_description="Hasil OCR yang berhasil diproses",
    responses={
        400: {"description": "File type tidak valid"},
        413: {"description": "File terlalu besar"},
        500: {"description": "Gagal memproses gambar"},
    },
)
async def create_ocr(
    file: Annotated[UploadFile, File(description="File gambar (jpeg/png/gif/webp/bmp)")],
    db: Annotated[AsyncSession, Depends(get_db)],
    ocr_service: Annotated[OcrService, Depends(get_ocr_service)],
):
    """
    Upload file gambar dan ekstrak teks menggunakan PaddleOCR. Hasil disimpan ke database dan dikembalikan ke user.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
        )

    try:
        # Save file
        filename, content = await save_upload_file(file)

        # Create pending record
        ocr_result = OcrResult(
            filename=filename,
            status="pending",
        )
        db.add(ocr_result)
        await db.flush()

        # Run OCR
        try:
            extracted_text = ocr_service.extract_text_from_bytes(content)
            ocr_result.extracted_text = extracted_text
            ocr_result.status = "completed"
        except ValueError:
            ocr_result.status = "failed"
            await db.commit()
            await db.refresh(ocr_result)
            raise HTTPException(
                status_code=500,
                detail="Failed to process image",
            )

        await db.commit()
        await db.refresh(ocr_result)

        return ocr_result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error processing OCR upload")
        raise HTTPException(status_code=500, detail="Failed to process image")


@router.get(
    "/{ocr_id}",
    response_model=OcrResultResponse,
    summary="Ambil hasil OCR berdasarkan ID",
    description="Ambil hasil OCR yang sudah diproses berdasarkan UUID.",
    response_description="Data hasil OCR",
    responses={
        404: {"description": "OCR result tidak ditemukan"},
    },
)
async def get_ocr_by_id(
    ocr_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Ambil hasil OCR berdasarkan UUID.
    """
    result = await db.execute(
        select(OcrResult).where(OcrResult.id == ocr_id)
    )
    ocr_result = result.scalar_one_or_none()

    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")

    return ocr_result


@router.get(
    "",
    response_model=OcrResultList,
    summary="List semua hasil OCR (pagination)",
    description="Menampilkan semua hasil OCR yang sudah diproses, dengan dukungan pagination dan filter status.",
    response_description="List hasil OCR",
    responses={
        200: {"description": "List hasil OCR"},
    },
)
async def list_ocr_results(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Nomor halaman")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Jumlah item per halaman")] = 10,
    status: Annotated[Optional[str], Query(description="Filter berdasarkan status (pending/completed/failed)")] = None,
):
    """
    List semua hasil OCR yang sudah diproses, dengan pagination dan filter status.
    """
    # Build query
    query = select(OcrResult)
    count_query = select(func.count(OcrResult.id))

    if status:
        query = query.where(OcrResult.status == status)
        count_query = count_query.where(OcrResult.status == status)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size

    # Get results
    query = query.order_by(OcrResult.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return OcrResultList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.delete(
    "/{ocr_id}",
    status_code=204,
    summary="Hapus hasil OCR berdasarkan ID",
    description="Hapus hasil OCR dari database berdasarkan UUID.",
    response_description="Berhasil dihapus (tanpa body)",
    responses={
        404: {"description": "OCR result tidak ditemukan"},
    },
)
async def delete_ocr(
    ocr_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Hapus hasil OCR dari database berdasarkan UUID.
    """
    result = await db.execute(
        select(OcrResult).where(OcrResult.id == ocr_id)
    )
    ocr_result = result.scalar_one_or_none()

    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")

    # Delete file if exists — ensure path stays within UPLOAD_DIR
    safe_filename = os.path.basename(ocr_result.filename)
    filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)
    resolved = os.path.realpath(filepath)
    upload_dir_resolved = os.path.realpath(settings.UPLOAD_DIR)
    if resolved.startswith(upload_dir_resolved) and os.path.exists(resolved):
        os.remove(resolved)

    await db.delete(ocr_result)
    await db.commit()

    return None
