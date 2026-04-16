from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(request: Request, api_key: str = Security(api_key_header)) -> None:
    """Verify API key if API_KEY is configured."""
    if not settings.API_KEY:
        return  # Auth disabled when no key is set
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
