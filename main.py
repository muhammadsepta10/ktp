from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import ocr_router, ktp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    await create_tables()
    yield
    # Shutdown: cleanup if needed
    pass


tags_metadata = [
    {"name": "Health", "description": "Health check endpoint"},
    {"name": "OCR", "description": "General OCR text extraction"},
    {"name": "KTP OCR", "description": "KTP Indonesia OCR extraction & parsing"},
]

# Conditionally expose OpenAPI docs only in debug mode
app = FastAPI(
    title="OCR API Service",
    description="REST API untuk ekstraksi teks dari gambar umum dan KTP Indonesia menggunakan PaddleOCR.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Tim Pengembang",
        "email": "dev@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_version="3.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# CORS middleware — use explicit origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(ocr_router)
app.include_router(ktp_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
