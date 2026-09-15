"""Domain exceptions.

This module has **no web-framework imports on purpose**. Business code raises a
`HirelensError`; it never builds an HTTP response. Translating these into HTTP
lives in `app/api/errors.py`, one layer up.

That separation is what lets services run outside of HTTP - in a background
worker, a CLI, or a test - and it gives the frontend one predictable envelope:

    {"error": {"code": "...", "message": "...", "details": {...}}}

`status_code` is carried here as plain data, not as an HTTP object.
"""
from typing import Any


class HirelensError(Exception):
    """Base class for every expected, handled failure in the application."""

    code: str = "internal_error"
    status_code: int = 500
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)

    def to_payload(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


# --- Document errors -------------------------------------------------------

class UnsupportedFileTypeError(HirelensError):
    code = "unsupported_file_type"
    status_code = 400
    message = "That file type is not supported."


class FileTooLargeError(HirelensError):
    code = "file_too_large"
    status_code = 413
    message = "The uploaded file is too large."


class CorruptDocumentError(HirelensError):
    code = "corrupt_document"
    status_code = 422
    message = "The document could not be read."


class EmptyDocumentError(HirelensError):
    code = "empty_document"
    status_code = 422
    message = "No readable text could be extracted from that document."


class DocumentNotFoundError(HirelensError):
    code = "document_not_found"
    status_code = 404
    message = "Document not found."


# --- Analysis / AI errors --------------------------------------------------

class ModuleNotFoundError_(HirelensError):
    code = "module_not_found"
    status_code = 404
    message = "Unknown analysis module."


class ModuleInputError(HirelensError):
    code = "module_input_error"
    status_code = 400
    message = "This analysis module is missing required input."


class AIUnavailableError(HirelensError):
    code = "ai_unavailable"
    status_code = 503
    message = "AI analysis is not configured on this server."


class AIResponseError(HirelensError):
    code = "ai_response_invalid"
    status_code = 502
    message = "The AI returned a response that failed validation."


class AICreditExhaustedError(HirelensError):
    code = "ai_credit_exhausted"
    status_code = 402
    message = (
        "The Anthropic account behind this app is out of credit, so the "
        "analysis could not run."
    )


class AIAuthError(HirelensError):
    code = "ai_auth_failed"
    status_code = 401
    message = "The Anthropic API key was rejected."


class AIRateLimitError(HirelensError):
    code = "ai_rate_limited"
    status_code = 429
    message = "Too many requests were sent to the AI in a short time."


class AIOverloadedError(HirelensError):
    code = "ai_overloaded"
    status_code = 503
    message = "The AI service is temporarily overloaded."
