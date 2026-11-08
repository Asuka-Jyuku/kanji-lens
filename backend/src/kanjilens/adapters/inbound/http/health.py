"""Health check route."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/api/health")
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok")
