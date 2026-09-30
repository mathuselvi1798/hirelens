"""Document persistence, behind an interface.

`PostgresDocumentStore` implements the same `DocumentStore` Protocol as
`InMemoryDocumentStore`. Nothing that calls a store changes, because callers
depend on the protocol, not the implementation - this is the seam the
original design was built around, and Phase 4 is the payoff: swap which
store `get_document_store()` returns, and every route, service, and test
that already depends on `DocumentStore` keeps working unmodified.
"""
from collections import OrderedDict
from typing import Annotated, Protocol

from fastapi import Depends
from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import JSON

from app.core.config import Settings, get_settings
from app.core.database import Base, get_session_factory
from app.core.exceptions import DocumentNotFoundError
from app.schemas.document import CanonicalDocument, ContactInfo, DocumentSection


class DocumentStore(Protocol):
    def save(self, document: CanonicalDocument) -> None: ...
    def get(self, document_id: str) -> CanonicalDocument: ...
    def list_recent(self, limit: int = 20) -> list[CanonicalDocument]: ...


class InMemoryDocumentStore:
    """Process-local store with a bounded size.

    Used whenever DATABASE_URL is unset - local dev without Postgres running,
    and every existing test, none of which override get_document_store.
    """

    def __init__(self, max_items: int = 200) -> None:
        self._items: OrderedDict[str, CanonicalDocument] = OrderedDict()
        self._max_items = max_items

    def save(self, document: CanonicalDocument) -> None:
        self._items[document.id] = document
        self._items.move_to_end(document.id)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)

    def get(self, document_id: str) -> CanonicalDocument:
        document = self._items.get(document_id)
        if document is None:
            raise DocumentNotFoundError(
                "That document is no longer available. Please upload it again."
            )
        return document

    def list_recent(self, limit: int = 20) -> list[CanonicalDocument]:
        return list(reversed(list(self._items.values())))[:limit]


class DocumentRecord(Base):
    """The `documents` table. Storage shape only - `CanonicalDocument` (in
    app.schemas.document) is the shape every module actually consumes."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    sections: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    bullets: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    contact: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


def _to_canonical(record: DocumentRecord) -> CanonicalDocument:
    return CanonicalDocument(
        id=record.id,
        filename=record.filename,
        file_type=record.file_type,  # type: ignore[arg-type]
        content_hash=record.content_hash,
        created_at=record.created_at,  # type: ignore[arg-type]
        raw_text=record.raw_text,
        sections=[DocumentSection(**s) for s in record.sections],
        bullets=list(record.bullets),
        contact=ContactInfo(**record.contact),
        word_count=record.word_count,
        page_count=record.page_count,
    )


class PostgresDocumentStore:
    """Real, durable storage. Every method opens one short-lived session,
    does its work, and closes it - no session is ever held across calls."""

    def __init__(self, session_factory: "sessionmaker[Session]") -> None:
        self._session_factory = session_factory

    def save(self, document: CanonicalDocument) -> None:
        with self._session_factory() as session:
            record = session.get(DocumentRecord, document.id)
            if record is None:
                record = DocumentRecord(id=document.id)
                session.add(record)

            record.filename = document.filename
            record.file_type = document.file_type
            record.content_hash = document.content_hash
            record.created_at = document.created_at
            record.raw_text = document.raw_text
            record.sections = [s.model_dump() for s in document.sections]
            record.bullets = list(document.bullets)
            record.contact = document.contact.model_dump()
            record.word_count = document.word_count
            record.page_count = document.page_count
            session.commit()

    def get(self, document_id: str) -> CanonicalDocument:
        with self._session_factory() as session:
            record = session.get(DocumentRecord, document_id)
            if record is None:
                raise DocumentNotFoundError(
                    "That document is no longer available. Please upload it again."
                )
            return _to_canonical(record)

    def list_recent(self, limit: int = 20) -> list[CanonicalDocument]:
        with self._session_factory() as session:
            stmt = (
                select(DocumentRecord)
                .order_by(DocumentRecord.created_at.desc())
                .limit(limit)
            )
            records = session.scalars(stmt).all()
            return [_to_canonical(r) for r in records]


_in_memory_store: DocumentStore = InMemoryDocumentStore()
_postgres_store: DocumentStore | None = None


def get_document_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentStore:
    """FastAPI dependency.

    Falls back to the in-memory store whenever DATABASE_URL is unset - which
    is exactly the test suite's situation (Settings() fixture leaves it
    blank), so every existing test keeps passing without touching Postgres.
    """
    global _postgres_store
    if not settings.database_url:
        return _in_memory_store
    if _postgres_store is None:
        _postgres_store = PostgresDocumentStore(get_session_factory(settings))
    return _postgres_store
