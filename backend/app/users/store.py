"""User persistence, behind an interface.

Same pattern as app.documents.store: a Protocol, an in-memory implementation
(used whenever DATABASE_URL is unset, including every existing test), a
Postgres implementation, and a get_user_store dependency that picks one.
"""
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Annotated, Protocol

from fastapi import Depends
from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import Base, get_session_factory


class User:
    """Plain in-memory representation, independent of storage."""

    def __init__(
        self, id: str, email: str, hashed_password: str, created_at: datetime
    ) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = created_at


class UserStore(Protocol):
    def create(self, email: str, hashed_password: str) -> User: ...
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_id(self, user_id: str) -> User | None: ...


class InMemoryUserStore:
    """Used whenever DATABASE_URL is unset - local dev without Postgres, and
    every existing test (none of which touch auth yet)."""

    def __init__(self) -> None:
        self._by_id: OrderedDict[str, User] = OrderedDict()

    def create(self, email: str, hashed_password: str) -> User:
        user = User(
            id=uuid.uuid4().hex,
            email=email,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
        )
        self._by_id[user.id] = user
        return user

    def get_by_email(self, email: str) -> User | None:
        for user in self._by_id.values():
            if user.email == email:
                return user
        return None

    def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)


class UserRecord(Base):
    """The `users` table."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


def _to_user(record: UserRecord) -> User:
    return User(
        id=record.id,
        email=record.email,
        hashed_password=record.hashed_password,
        created_at=record.created_at,  # type: ignore[arg-type]
    )


class PostgresUserStore:
    """Real, durable storage. Every method opens one short-lived session,
    does its work, and closes it - no session is ever held across calls."""

    def __init__(self, session_factory: "sessionmaker[Session]") -> None:
        self._session_factory = session_factory

    def create(self, email: str, hashed_password: str) -> User:
        with self._session_factory() as session:
            record = UserRecord(
                id=uuid.uuid4().hex,
                email=email,
                hashed_password=hashed_password,
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_user(record)

    def get_by_email(self, email: str) -> User | None:
        with self._session_factory() as session:
            record = session.scalars(
                select(UserRecord).where(UserRecord.email == email)
            ).first()
            return _to_user(record) if record else None

    def get_by_id(self, user_id: str) -> User | None:
        with self._session_factory() as session:
            record = session.get(UserRecord, user_id)
            return _to_user(record) if record else None


_in_memory_user_store: UserStore = InMemoryUserStore()
_postgres_user_store: UserStore | None = None


def get_user_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserStore:
    """FastAPI dependency. Falls back to the in-memory store whenever
    DATABASE_URL is unset, exactly like get_document_store."""
    global _postgres_user_store
    if not settings.database_url:
        return _in_memory_user_store
    if _postgres_user_store is None:
        _postgres_user_store = PostgresUserStore(get_session_factory(settings))
    return _postgres_user_store
