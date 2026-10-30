from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings

app = FastAPI(
    title=settings.app_name,
    description="Software change impact intelligence API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="changeradar-api", version="0.1.0")


@app.get(f"{settings.api_v1_prefix}/status", tags=["system"])
async def api_status() -> dict[str, str]:
    return {"message": "ChangeRadar API is ready", "environment": settings.environment}
