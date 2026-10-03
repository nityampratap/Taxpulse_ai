from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str = "taxpulse-ai"


class ReadinessResponse(BaseModel):
    status: str
    database: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="healthy", service="taxpulse-ai")


@router.get("/health/ready", response_model=ReadinessResponse)
def get_readiness() -> ReadinessResponse:
    return ReadinessResponse(status="ready", database="connected", environment="development")
