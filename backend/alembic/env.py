"""Alembic environment script.

Wired to the app's own Settings and models, rather than a URL hard-coded in
alembic.ini. This way there is exactly one place the database connection
string lives (backend/.env) and Alembic always migrates the same database
the app itself connects to.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make "app.xxx" importable when Alembic is run from the backend/ folder.
from app.core.config import get_settings
from app.core.database import Base

# Import every module that defines an ORM model, purely for its side effect
# of registering the model's table on Base.metadata. Autogenerate can only
# see tables that have actually been imported by the time this file runs -
# forgetting an import here is the classic way to get an empty migration.
from app.documents import store as _documents_store  # noqa: F401
from app.users import store as _users_store  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The app's own settings are the source of truth for the connection string -
# alembic.ini keeps a placeholder that is never actually used.
settings = get_settings()
if settings.database_url:
    config.set_main_option("sqlalchemy.url", settings.database_url)

# Every model's table, discovered via the imports above.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
