"""Signup, login, and "who am I" endpoints.

Issues a JWT on signup/login; every other protected route reads that token
via `get_current_user` (app.api.deps) rather than a server-side session -
this keeps the API stateless, matching how Phase 4 (Postgres) and Phase 7
(analysis modules) were both built.
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.users.store import User, UserStore, get_user_store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(
    request: SignupRequest,
    store: Annotated[UserStore, Depends(get_user_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    if store.get_by_email(request.email) is not None:
        raise EmailAlreadyRegisteredError()

    user = store.create(request.email, hash_password(request.password))
    token = create_access_token(subject=user.id, settings=settings)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, created_at=user.created_at),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    store: Annotated[UserStore, Depends(get_user_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    user = store.get_by_email(request.email)
    if user is None or not verify_password(request.password, user.hashed_password):
        raise InvalidCredentialsError()

    token = create_access_token(subject=user.id, settings=settings)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, created_at=user.created_at),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut(
        id=current_user.id, email=current_user.email, created_at=current_user.created_at
    )
