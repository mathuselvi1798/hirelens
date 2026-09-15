"""Health and capability reporting.

`/health` is a liveness probe. `/health/capabilities` tells the frontend what
this server can actually do, so the UI can disable AI features with an honest
message instead of letting the user click a button that will fail.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.ai.client import AIClient, get_ai_client
from app.analysis.registry import all_modules
from app.core.config import Settings, get_settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    version: str


class CapabilitiesResponse(BaseModel):
    ai_enabled: bool
    ai_provider: str
    module_count: int
    max_upload_mb: int
    allowed_extensions: list[str]


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    from app import __version__

    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.environment,
        version=__version__,
    )


@router.get("/health/capabilities", response_model=CapabilitiesResponse)
def capabilities(
    settings: Annotated[Settings, Depends(get_settings)],
    ai: Annotated[AIClient, Depends(get_ai_client)],
) -> CapabilitiesResponse:
    return CapabilitiesResponse(
        ai_enabled=ai.enabled,
        ai_provider=ai.provider_name,
        module_count=len(all_modules()),
        max_upload_mb=settings.max_upload_mb,
        allowed_extensions=sorted(settings.allowed_extensions),
    )
