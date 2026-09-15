"""Document persistence, behind an interface.

Phase 4 will add `PostgresDocumentStore` implementing this same protocol and
swap it in `get_document_store()`. Nothing that calls a store will change,
because callers depend on the protocol, not the implementation. This is the
seam that lets us defer the database without painting ourselves into a corner.
"""
from collections import OrderedDict
from typing import Protocol

from app.core.exceptions import DocumentNotFoundError
from app.schemas.document import CanonicalDocument


class DocumentStore(Protocol):
    def save(self, document: CanonicalDocument) -> None: ...
    def get(self, document_id: str) -> CanonicalDocument: ...
    def list_recent(self, limit: int = 20) -> list[CanonicalDocument]: ...


class InMemoryDocumentStore:
    """Process-local store with a bounded size.

    Deliberately simple and deliberately temporary. Documents disappear on
    restart - acceptable in development, and replaced in Phase 4.
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


_store: DocumentStore = InMemoryDocumentStore()


def get_document_store() -> DocumentStore:
    """FastAPI dependency. Phase 4 changes this one function."""
    return _store
