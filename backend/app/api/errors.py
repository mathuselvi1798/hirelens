"""Translates domain errors into HTTP responses.

This is the only place that knows a `NexaError` becomes a status code. Keeping
it here - rather than in `app/core/exceptions.py` - means the domain layer has
no dependency on FastAPI, so services remain usable from a worker or a CLI.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import NexaError
from app.core.logging import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NexaError)
    async def _nexa_error_handler(_: Request, exc: NexaError) -> JSONResponse:
        logger.warning(
            "handled_error", code=exc.code, message=exc.message, details=exc.details
        )
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "The request was not valid.",
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        # Never leak internals to the client.
        logger.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )
