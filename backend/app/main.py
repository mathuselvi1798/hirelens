"""Application entrypoint.

An app *factory*, not a module-level app with logic bolted on. Tests build
their own instance with their own settings, which is what keeps the test suite
fast and isolated.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.analysis.registry import all_modules, discover
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger

from app.api.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    logger = get_logger("nexa.startup")

    # Import every analysis module once, at startup, so a broken module fails
    # loudly here rather than on a user's first request.
    discover()

    logger.info(
        "startup",
        app=settings.app_name,
        environment=settings.environment,
        ai_enabled=settings.ai_enabled,
        modules=[m.id for m in all_modules()],
    )
    if not settings.ai_enabled:
        logger.warning(
            "ai_disabled",
            hint="Set ANTHROPIC_API_KEY in backend/.env to enable AI analysis.",
        )
    yield
    logger.info("shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered career intelligence API.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    return app


app = create_app()
