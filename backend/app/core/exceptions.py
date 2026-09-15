"""Domain exceptions.

This module has **no web-framework imports on purpose**. Business code raises a
`NexaError`; it never builds an HTTP response. Translating these into HTTP
lives in `app/api/errors.py`, one layer up.

That separation is what lets services run outside of HTTP - in a background
worker, a CLI, or a test - and it gives the frontend one predictable envelope:

    {"error": {"code": "...", "message": "...", "details": {...}}}

`status_code` is carried here as plain data, not as an HTTP object.
"""
from typing import Any


class NexaError(Exception):
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

class UnsupportedFileTypeError(NexaError):
    code = "unsupported_file_type"
    status_code = 400
    message = "That file type is not supported."


class FileTooLargeError(NexaError):
    code = "file_too_large"
    status_code = 413
    message = "The uploaded file is too large."


class CorruptDocumentError(NexaError):
    code = "corrupt_document"
    status_code = 422
    message = "The document could not be read."


class EmptyDocumentError(NexaError):
    code = "empty_document"
    status_code = 422
    message = "No readable text could be extracted from that document."


class DocumentNotFoundError(NexaError):
    code = "document_not_found"
    status_code = 404
    message = "Document not found."


# --- Analysis / AI errors --------------------------------------------------

class ModuleNotFoundError_(NexaError):
    code = "module_not_found"
    status_code = 404
    message = "Unknown analysis module."


class ModuleInputError(NexaError):
    code = "module_input_error"
    status_code = 400
    message = "This analysis module is missing required input."


class AIUnavailableError(NexaError):
    code = "ai_unavailable"
    status_code = 503
    message = "AI analysis is not configured on this server."


class AIResponseError(NexaError):
    code = "ai_response_invalid"
    status_code = 502
    message = "The AI returned a response that failed validation."


class AICreditExhaustedError(NexaError):
    code = "ai_credit_exhausted"
    status_code = 402
    message = (
        "The Anthropic account behind this app is out of credit, so the "
        "analysis could not run."
    )


class AIAuthError(NexaError):
    code = "ai_auth_failed"
    status_code = 401
    message = "The Anthropic API key was rejected."


class AIRateLimitError(NexaError):
    code = "ai_rate_limited"
    status_code = 429
    message = "Too many requests were sent to the AI in a short time."


class AIOverloadedError(NexaError):
    code = "ai_overloaded"
    status_code = 503
    message = "The AI service is temporarily overloaded."
