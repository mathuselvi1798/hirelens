"""Password hashing and JWT helpers for authentication.

Kept separate from app/users/store.py (storage) and the auth routes (HTTP) -
this module only knows about hashing and tokens, nothing about the database
or FastAPI.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import Settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(*, subject: str, settings: Settings) -> str:
    """`subject` is the user id. Encodes it plus an expiry into a signed JWT."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> str:
    """Returns the user id (subject) encoded in the token.

    Raises jwt.PyJWTError (expired, bad signature, malformed) - callers
    translate that into an HTTP 401 at the API boundary.
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return payload["sub"]
