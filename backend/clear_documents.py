"""One-off cleanup: wipe all rows from the documents table.

Run from the backend/ folder with the project's virtualenv active (or via
clear-documents.bat, which does this for you). Uses the same DATABASE_URL as
the app itself, so it always targets the real Hirelens database.
"""
from app.core.config import get_settings
from app.core.database import get_engine
from app.documents.store import DocumentRecord
from sqlalchemy import delete, select, func

settings = get_settings()
if not settings.database_url:
    raise SystemExit("DATABASE_URL is not set - nothing to clean up.")

engine = get_engine(settings)

with engine.begin() as conn:
    count_before = conn.execute(select(func.count()).select_from(DocumentRecord)).scalar_one()
    conn.execute(delete(DocumentRecord))
    count_after = conn.execute(select(func.count()).select_from(DocumentRecord)).scalar_one()

print(f"Deleted {count_before} document(s). Rows remaining: {count_after}.")
