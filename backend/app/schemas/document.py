"""API-facing schemas for documents.

These are deliberately separate from any future database model. A DB model
describes how data is *stored*; these describe the *contract* with the
frontend. Letting one class do both jobs is how a codebase becomes impossible
to change.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FileType = Literal["pdf", "docx", "txt"]


class ContactInfo(BaseModel):
    email: str | None = None
    phone: str | None = None
    links: list[str] = Field(default_factory=list)


class DocumentSection(BaseModel):
    """A detected logical section of a resume, e.g. "experience"."""

    name: str = Field(description="Normalized section key, e.g. 'experience'")
    heading: str = Field(description="The heading exactly as written in the document")
    content: str = Field(default="", description="Raw text under the heading")
    line_start: int = 0


class CanonicalDocument(BaseModel):
    """The single structured representation every analysis module consumes.

    A file is parsed into this shape exactly once. Modules never touch the
    original upload, which means N analyses cost one parse, and re-running an
    analysis never requires re-uploading.
    """

    id: str
    filename: str
    file_type: FileType
    content_hash: str = Field(description="SHA-256 of extracted text; used for caching")
    created_at: datetime

    raw_text: str
    sections: list[DocumentSection] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    contact: ContactInfo = Field(default_factory=ContactInfo)

    word_count: int = 0
    page_count: int | None = None


class DocumentSummary(BaseModel):
    """What the API returns after an upload - the full raw text is not echoed
    back, because the frontend does not need it and it bloats responses."""

    id: str
    filename: str
    file_type: FileType
    created_at: datetime
    word_count: int
    page_count: int | None = None
    section_names: list[str] = Field(default_factory=list)
    bullet_count: int = 0
    contact: ContactInfo = Field(default_factory=ContactInfo)
    text_preview: str = ""

    @classmethod
    def from_document(cls, doc: CanonicalDocument) -> "DocumentSummary":
        preview = doc.raw_text[:400].strip()
        if len(doc.raw_text) > 400:
            preview += "..."
        return cls(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            created_at=doc.created_at,
            word_count=doc.word_count,
            page_count=doc.page_count,
            section_names=[s.name for s in doc.sections],
            bullet_count=len(doc.bullets),
            contact=doc.contact,
            text_preview=preview,
        )
