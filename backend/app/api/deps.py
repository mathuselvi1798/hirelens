"""Shared FastAPI dependencies that read the request itself (as opposed to
config or the database) - currently just "who is making this request".
"""
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import NotAuthenticatedError
from app.core.security import decode_access_token
from app.users.store import User, UserStore, get_user_store

# auto_error=False so a missing header raises our own HirelensError (and its
# {"error": {...}} envelope) instead of FastAPI's default 403 HTTPException.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[UserStore, Depends(get_user_store)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    """Reads the `Authorization: Bearer <token>` header, verifies the JWT,
    and loads the user it names. Any route that depends on this becomes a
    protected route."""
    if credentials is None:
        raise NotAuthenticatedError()

    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except jwt.PyJWTError:
        raise NotAuthenticatedError("Your session has expired. Please log in again.")

    user = store.get_by_id(user_id)
    if user is None:
        raise NotAuthenticatedError()
    return user
