"""API-facing schemas for the analysis engine."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModuleInfo(BaseModel):
    """Describes one registered analysis module to the frontend.

    The frontend renders its module picker from this list, so adding a new
    backend module makes it appear in the UI with no frontend release.
    """

    id: str
    version: str
    title: str
    description: str
    requires_job_description: bool = False
    category: str = "general"


class AnalysisRequest(BaseModel):
    document_id: str = Field(description="ID returned by POST /documents")
    job_description: str | None = Field(
        default=None, max_length=30_000, description="Required by some modules"
    )
    options: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Envelope around a module's validated output.

    `data` is the module's own Pydantic model, already validated. The envelope
    is identical for every module, which is what lets the frontend route
    results generically.
    """

    id: str
    module_id: str
    module_version: str
    prompt_version: str
    document_id: str
    created_at: datetime
    duration_ms: int
    cached: bool = False
    data: dict[str, Any]
