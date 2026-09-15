"""The boundary between this application and any LLM vendor.

Everything above this line thinks in terms of "give me an object matching this
JSON schema". Only the implementations below know about a vendor SDK. Adding
OpenAI later means writing one class here and changing one line of config -
no module, route, or prompt changes.
"""
from typing import Any, Protocol

from app.core.exceptions import AIUnavailableError


class AIProvider(Protocol):
    name: str

    def generate_json(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict[str, Any],
        schema_name: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Return a dict conforming to `json_schema`, or raise an AI error."""
        ...


class NullProvider:
    """Used when no API key is configured.

    Importantly, the application still starts and every non-AI endpoint still
    works - only AI-backed calls fail, with a clear, actionable 503.
    """

    name = "null"

    def generate_json(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict[str, Any],
        schema_name: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        raise AIUnavailableError(
            "AI analysis is not configured. Set ANTHROPIC_API_KEY in backend/.env "
            "and restart the server."
        )
