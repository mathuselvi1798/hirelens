"""Runs a registered module against a document.

Identical for every module - that uniformity is what the registry buys us.
"""
import time
import uuid
from datetime import datetime, timezone

from app.ai.cache import build_cache_key
from app.ai.client import AIClient
from app.analysis.base import AnalysisContext
from app.analysis.registry import get_module
from app.core.exceptions import ModuleInputError
from app.core.logging import get_logger
from app.schemas.analysis import AnalysisResult

logger = get_logger(__name__)


def run_analysis(
    *, module_id: str, ctx: AnalysisContext, ai: AIClient
) -> AnalysisResult:
    module = get_module(module_id)

    if module.requires_job_description and not (ctx.job_description or "").strip():
        raise ModuleInputError(
            f"'{module.title}' requires a job description. Paste one and try again."
        )

    system, user = module.build_prompt(ctx)
    cache_key = build_cache_key(
        content_hash=ctx.document.content_hash,
        module_id=module.id,
        prompt_version=module.prompt_version,
        extra=module.cache_extra(ctx),
    )

    started = time.perf_counter()
    result, cached = ai.generate(
        model_cls=module.output_model,
        system=system,
        user=user,
        cache_key=cache_key,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)

    logger.info(
        "analysis_complete",
        module_id=module.id,
        document_id=ctx.document.id,
        duration_ms=duration_ms,
        cached=cached,
    )

    return AnalysisResult(
        id=uuid.uuid4().hex,
        module_id=module.id,
        module_version=module.version,
        prompt_version=module.prompt_version,
        document_id=ctx.document.id,
        created_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        cached=cached,
        data=result.model_dump(mode="json"),
    )
