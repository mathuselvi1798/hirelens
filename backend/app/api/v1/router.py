"""Aggregates every v1 route module into one router."""
from fastapi import APIRouter

from app.api.v1.routes import analysis, documents, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(analysis.router)
