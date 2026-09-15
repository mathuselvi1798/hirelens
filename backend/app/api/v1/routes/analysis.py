"""Analysis endpoints.

There is one run endpoint for every analysis module, present and future. The
module id is a path parameter, so adding "interview_questions" later adds a
working endpoint automatically.
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.client import AIClient, get_ai_client
from app.analysis.base import AnalysisContext
from app.analysis.registry import all_modules
from app.analysis.service import run_analysis
from app.documents.store import DocumentStore, get_document_store
from app.schemas.analysis import AnalysisRequest, AnalysisResult, ModuleInfo

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/modules", response_model=list[ModuleInfo])
def list_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(
            id=m.id,
            version=m.version,
            title=m.title,
            description=m.description,
            requires_job_description=m.requires_job_description,
            category=m.category,
        )
        for m in all_modules()
    ]


@router.post("/{module_id}/run", response_model=AnalysisResult)
def run_module(
    module_id: str,
    request: AnalysisRequest,
    store: Annotated[DocumentStore, Depends(get_document_store)],
    ai: Annotated[AIClient, Depends(get_ai_client)],
) -> AnalysisResult:
    document = store.get(request.document_id)
    ctx = AnalysisContext(
        document=document,
        job_description=request.job_description,
        options=request.options,
    )
    return run_analysis(module_id=module_id, ctx=ctx, ai=ai)
