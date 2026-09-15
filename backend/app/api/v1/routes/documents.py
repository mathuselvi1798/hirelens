"""Document endpoints.

These handlers are deliberately thin: read the request, call a service,
shape the response. No parsing logic, no validation rules, no business
decisions live here.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings, get_settings
from app.documents import service
from app.documents.store import DocumentStore, get_document_store
from app.schemas.document import DocumentSummary

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentSummary, status_code=201)
async def upload_document(
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[DocumentStore, Depends(get_document_store)],
    file: UploadFile = File(..., description="Resume as PDF, DOCX, or TXT"),
) -> DocumentSummary:
    data = await file.read()
    document = service.ingest(file.filename or "resume", data, settings, store)
    return DocumentSummary.from_document(document)


@router.get("", response_model=list[DocumentSummary])
def list_documents(
    store: Annotated[DocumentStore, Depends(get_document_store)],
    limit: int = 20,
) -> list[DocumentSummary]:
    return [DocumentSummary.from_document(d) for d in store.list_recent(limit)]


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(
    document_id: str,
    store: Annotated[DocumentStore, Depends(get_document_store)],
) -> DocumentSummary:
    return DocumentSummary.from_document(store.get(document_id))
