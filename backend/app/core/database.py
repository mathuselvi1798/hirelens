"""SQLAlchemy engine and session management.

A single Engine is created once per process and reused. Sessions are
short-lived: opened per unit of work, closed immediately after, never held
across requests.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    """Base class for every ORM model in the app."""


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    """Cached engine accessor. Created once, reused for the process lifetime."""
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    """Cached sessionmaker, bound to the shared engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(settings), autoflush=False, autocommit=False
        )
    return _session_factory


def create_all_tables(settings: Settings | None = None) -> None:
    """Create any tables that don't exist yet, from the current ORM models.

    This is a dev-friendly stand-in for a migration tool: fine while there is
    no real data and the schema is still moving. Once the app has users and
    the schema needs to change safely, add Alembic and stop calling this.
    """
    Base.metadata.create_all(bind=get_engine(settings))


def reset_engine_cache() -> None:
    """Test/dev helper: forces the next get_engine()/get_session_factory()
    call to build fresh ones, picking up a changed DATABASE_URL."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
