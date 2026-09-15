"""The contract every analysis module implements.

A module declares what it needs, what it produces, and how to ask for it.
It does not know about HTTP, the database, caching, retries, or which LLM
vendor is configured. That is the whole reason a twelfth module will cost
roughly what the second one cost.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from app.schemas.document import CanonicalDocument


@dataclass
class AnalysisContext:
    """Everything a module is allowed to see."""

    document: CanonicalDocument
    job_description: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


class AnalysisModule(ABC):
    # --- Identity (surfaced to the frontend) -------------------------------
    id: str
    version: str = "1.0"
    title: str
    description: str
    category: str = "general"

    # --- Contract ----------------------------------------------------------
    requires_job_description: bool = False
    output_model: type[BaseModel]

    # Bump this whenever the prompt changes; it invalidates cached results.
    prompt_version: str = "1"

    @abstractmethod
    def build_prompt(self, ctx: AnalysisContext) -> tuple[str, str]:
        """Return `(system_prompt, user_prompt)`."""
        raise NotImplementedError

    def cache_extra(self, ctx: AnalysisContext) -> str:
        """Extra inputs beyond the document that affect the result.

        Modules that use the job description must include it here, or two
        different jobs would share one cached answer.
        """
        return ctx.job_description or ""
