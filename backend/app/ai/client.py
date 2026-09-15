"""The AI service layer.

Modules never import a vendor SDK. They hand this client a Pydantic model and
a prompt; they get back a validated instance of that model or a domain error.
Retries, caching, schema enforcement, and logging all live here, once, instead
of being reimplemented in every module.
"""
import time
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.cache import InMemoryResultCache, build_cache_key
from app.ai.provider import AIProvider, NullProvider
from app.core.config import Settings
from app.core.exceptions import (
    AIOverloadedError,
    AIRateLimitError,
    AIResponseError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# How many times to retry a provider outage or rate limit before giving up.
TRANSIENT_ATTEMPTS = 3


def _tool_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Pydantic's JSON schema, flattened for tool-use.

    `$defs`/`$ref` are inlined because tool input schemas are consumed more
    reliably when self-contained.
    """
    schema = model_cls.model_json_schema()
    defs = schema.pop("$defs", {})

    def inline(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                ref_name = node["$ref"].split("/")[-1]
                target = defs.get(ref_name, {})
                merged = {k: v for k, v in node.items() if k != "$ref"}
                return inline({**target, **merged})
            return {k: inline(v) for k, v in node.items()}
        if isinstance(node, list):
            return [inline(item) for item in node]
        return node

    return inline(schema)


class AIClient:
    def __init__(
        self,
        provider: AIProvider,
        settings: Settings,
        cache: InMemoryResultCache | None = None,
    ) -> None:
        self._provider = provider
        self._settings = settings
        self._cache = cache or InMemoryResultCache()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def enabled(self) -> bool:
        return not isinstance(self._provider, NullProvider)

    def _call_with_transient_retry(
        self, *, system: str, user: str, schema: dict[str, Any], schema_name: str
    ) -> dict[str, Any]:
        """Retry provider outages and rate limits, but never real errors.

        A 503 or a rate limit is the provider having a moment; retrying costs a
        second and usually succeeds. A bad key or a rejected schema will fail
        identically every time, so those propagate immediately rather than
        making the user wait through pointless retries.
        """
        attempts = TRANSIENT_ATTEMPTS
        for attempt in range(1, attempts + 1):
            try:
                return self._provider.generate_json(
                    system=system,
                    user=user,
                    json_schema=schema,
                    schema_name=schema_name,
                    max_tokens=self._settings.ai_max_tokens,
                )
            except (AIOverloadedError, AIRateLimitError) as exc:
                if attempt == attempts:
                    raise
                delay = _transient_backoff(attempt)
                logger.warning(
                    "ai_transient_retry",
                    code=exc.code,
                    attempt=attempt,
                    retrying_in_seconds=delay,
                )
                time.sleep(delay)
        raise AIResponseError("The AI request could not be completed.")

    def generate(
        self,
        *,
        model_cls: type[T],
        system: str,
        user: str,
        cache_key: str | None = None,
    ) -> tuple[T, bool]:
        """Return `(validated_result, was_cached)`."""
        if cache_key and self._settings.ai_cache_enabled:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.info("ai_cache_hit", cache_key=cache_key)
                return model_cls.model_validate(cached), True

        schema = _tool_schema(model_cls)
        schema_name = _snake(model_cls.__name__)
        attempts = max(1, self._settings.ai_max_retries + 1)
        last_error: str = ""
        current_user = user

        for attempt in range(1, attempts + 1):
            raw = self._call_with_transient_retry(
                system=system,
                user=current_user,
                schema=schema,
                schema_name=schema_name,
            )
            try:
                result = model_cls.model_validate(raw)
            except ValidationError as exc:
                last_error = _short_errors(exc)
                logger.warning(
                    "ai_validation_failed",
                    attempt=attempt,
                    schema=schema_name,
                    errors=last_error,
                )
                # Feed the failure back so the retry is informed, not blind.
                current_user = (
                    f"{user}\n\n---\nYour previous response was rejected by schema "
                    f"validation with these errors:\n{last_error}\n"
                    "Return a corrected response that satisfies every constraint."
                )
                continue

            if cache_key and self._settings.ai_cache_enabled:
                self._cache.set(cache_key, result.model_dump(mode="json"))
            logger.info("ai_call_ok", schema=schema_name, attempt=attempt)
            return result, False

        raise AIResponseError(
            "The AI response failed validation after several attempts.",
            details={"schema": schema_name, "errors": last_error},
        )


def _transient_backoff(attempt: int) -> float:
    """1s, then 3s. Short enough that a user waits, long enough to clear a blip."""
    return (1.0, 3.0)[min(attempt - 1, 1)]


def _snake(name: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _short_errors(exc: ValidationError, limit: int = 8) -> str:
    lines = []
    for err in exc.errors()[:limit]:
        loc = ".".join(str(p) for p in err.get("loc", ()))
        lines.append(f"- {loc}: {err.get('msg')}")
    return "\n".join(lines)


# --- Wiring ----------------------------------------------------------------

_cache = InMemoryResultCache()
_client: AIClient | None = None


def build_provider(settings: Settings) -> AIProvider:
    """Pick the provider named in configuration.

    This function is the entire cost of supporting another vendor. Nothing
    else in the application knows which one is in use.
    """
    if not settings.ai_enabled:
        return NullProvider()

    if settings.ai_provider == "gemini":
        from app.ai.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_seconds=settings.ai_timeout_seconds,
        )

    from app.ai.anthropic_provider import AnthropicProvider

    return AnthropicProvider(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        timeout_seconds=settings.ai_timeout_seconds,
    )


def get_ai_client() -> AIClient:
    """FastAPI dependency; the client is built once per process."""
    global _client
    if _client is None:
        from app.core.config import get_settings

        settings = get_settings()
        _client = AIClient(build_provider(settings), settings, _cache)
    return _client


def reset_ai_client() -> None:
    """Test hook - forces the next `get_ai_client()` to rebuild."""
    global _client
    _client = None
    _cache.clear()
