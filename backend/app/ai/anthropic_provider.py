"""Anthropic implementation of `AIProvider`.

Structured output is enforced with forced tool use rather than by asking the
model to "reply with JSON". The model must call a tool whose input schema is
our Pydantic schema, so the response arrives as a parsed object instead of a
string we have to scrape. This removes an entire class of parsing bugs.

Vendor errors are translated into our own domain errors here. A raw SDK
exception is useful in a log and useless - often alarming - in a user
interface, so the full detail is logged and a plain, actionable message is
what travels onwards.
"""
from typing import Any

from app.core.exceptions import (
    AIAuthError,
    AICreditExhaustedError,
    AIOverloadedError,
    AIRateLimitError,
    AIResponseError,
    AIUnavailableError,
    HirelensError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def classify_provider_error(exc: Exception) -> HirelensError:
    """Turn a vendor exception into a domain error the UI can act on.

    Matching on both the status code and the message text is deliberate: SDK
    exception classes change between releases, message wording is stable
    enough for the handful of cases that matter, and a wrong guess here
    degrades to a generic error rather than a crash.
    """
    text = str(exc).lower()
    status = getattr(exc, "status_code", None)

    if "credit balance is too low" in text or "purchase credits" in text:
        return AICreditExhaustedError()

    if status == 401 or "authentication" in text or "invalid x-api-key" in text:
        return AIAuthError(
            "The Anthropic API key was rejected. It may be wrong, revoked, "
            "or expired - install a new one with set-api-key.bat."
        )

    if status == 429 or "rate limit" in text:
        return AIRateLimitError()

    if status in (500, 502, 503, 529) or "overloaded" in text:
        return AIOverloadedError()

    return AIResponseError("The AI request could not be completed. Please try again.")


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 90) -> None:
        if not api_key.strip():
            raise AIUnavailableError("No Anthropic API key configured.")
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise AIUnavailableError(
                "The 'anthropic' package is not installed on the server."
            ) from exc

        self._client = anthropic.Anthropic(api_key=api_key, timeout=float(timeout_seconds))
        self._model = model

    def generate_json(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict[str, Any],
        schema_name: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[
                    {
                        "name": schema_name,
                        "description": (
                            f"Submit the completed {schema_name} analysis. "
                            "Every field is required."
                        ),
                        "input_schema": json_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": schema_name},
            )
        except Exception as exc:
            error = classify_provider_error(exc)
            # Full detail to the log, clean message to the user.
            logger.error(
                "ai_call_failed",
                model=self._model,
                code=error.code,
                detail=str(exc),
            )
            raise error from exc

        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)  # type: ignore[arg-type]

        raise AIResponseError("The AI did not return structured output.")
