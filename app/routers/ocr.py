import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.ocr_result import OcrResult
from app.schemas.ocr import OcrResultResponse, OcrResultList
from app.services.ocr_service import get_ocr_service, OcrService
from app.config import settings

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"])


async def save_upload_file(upload_file: UploadFile) -> tuple[str, bytes]:
    """Save uploaded file and return path and content."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    ext = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".png"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    # Read content
    content = await upload_file.read()

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
        500: {"description": "Gagal memproses gambar"},
    },
)
async def create_ocr(
    file: UploadFile = File(..., description="File gambar (jpeg/png/gif/webp/bmp)"),
    db: AsyncSession = Depends(get_db),
    ocr_service: OcrService = Depends(get_ocr_service),
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
        except ValueError as e:
            ocr_result.status = "failed"
            ocr_result.extracted_text = str(e)

        await db.commit()
        await db.refresh(ocr_result)

        return ocr_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


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
    db: AsyncSession = Depends(get_db),
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
    page: int = Query(1, ge=1, description="Nomor halaman", example=1),
    page_size: int = Query(10, ge=1, le=100, description="Jumlah item per halaman", example=10),
    status: Optional[str] = Query(None, description="Filter berdasarkan status (pending/completed/failed)", example="completed"),
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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

    # Delete file if exists
    filepath = os.path.join(settings.UPLOAD_DIR, ocr_result.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    await db.delete(ocr_result)
    await db.commit()

    return None
