"""Document ingestion: validate -> extract -> structure -> store.

This is business logic, so it lives here rather than in a route. It raises
domain errors and knows nothing about HTTP.
"""
import hashlib
import uuid
from datetime import datetime, timezone

from app.core.config import Settings
from app.core.exceptions import EmptyDocumentError, FileTooLargeError, UnsupportedFileTypeError
from app.core.logging import get_logger
from app.documents import extractors, structure
from app.documents.store import DocumentStore
from app.schemas.document import CanonicalDocument

logger = get_logger(__name__)

MIN_USEFUL_CHARS = 100


def validate_upload(filename: str, size: int, settings: Settings) -> None:
    """Cheap checks first, before we spend CPU on parsing."""
    if size == 0:
        raise EmptyDocumentError("That file is empty.")

    if size > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"That file is {size / 1_048_576:.1f}MB. The limit is "
            f"{settings.max_upload_mb}MB."
        )

    lowered = filename.lower()
    if not any(lowered.endswith(ext) for ext in settings.allowed_extensions):
        allowed = ", ".join(sorted(settings.allowed_extensions))
        raise UnsupportedFileTypeError(
            f"'{filename}' is not an accepted file type. Allowed: {allowed}."
        )


def build_document(filename: str, data: bytes) -> CanonicalDocument:
    """Parse raw bytes into the canonical structure every module consumes."""
    file_type, raw_text, page_count = extractors.extract(filename, data)
    cleaned = raw_text.strip()

    if len(cleaned) < MIN_USEFUL_CHARS:
        raise EmptyDocumentError(
            "Almost no readable text could be extracted. If this is a scanned "
            "or image-based PDF, export a text-based PDF or DOCX and try again."
        )

    document = CanonicalDocument(
        id=uuid.uuid4().hex,
        filename=filename,
        file_type=file_type,  # type: ignore[arg-type]
        content_hash=hashlib.sha256(cleaned.encode("utf-8")).hexdigest(),
        created_at=datetime.now(timezone.utc),
        raw_text=cleaned,
        sections=structure.detect_sections(cleaned),
        bullets=structure.extract_bullets(cleaned),
        contact=structure.extract_contact(cleaned),
        word_count=structure.count_words(cleaned),
        page_count=page_count,
    )

    logger.info(
        "document_ingested",
        document_id=document.id,
        file_type=file_type,
        word_count=document.word_count,
        sections=[s.name for s in document.sections],
        bullets=len(document.bullets),
    )
    return document


def ingest(
    filename: str, data: bytes, settings: Settings, store: DocumentStore
) -> CanonicalDocument:
    validate_upload(filename, len(data), settings)
    document = build_document(filename, data)
    store.save(document)
    return document
