from fastapi import APIRouter, Depends
from models.schemas import HealthResponse
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service="i-hate-pdfs")
