"""Google Gemini implementation of `AIProvider`.

Included because Gemini has a genuine free tier, which makes this project
runnable at zero cost. Structured output uses `responseSchema`, Gemini's
equivalent of forced tool use, so the same validation guarantees hold.

Called over plain HTTP with httpx rather than through a vendor SDK: it is one
endpoint, and it keeps the dependency list short. The API key travels in a
header, never in the URL, so it cannot leak into logs or proxies.
"""
import json
from typing import Any

import httpx

from app.ai.schema_compat import to_gemini_schema
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

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def classify_gemini_error(status: int, body: str) -> HirelensError:
    text = body.lower()

    if status in (401, 403) or "api key not valid" in text or "api_key_invalid" in text:
        return AIAuthError(
            "Google rejected the API key. Create a new one in Google AI Studio "
            "and install it with set-gemini-key.bat."
        )
    if status == 429 or "resource_exhausted" in text or "quota" in text:
        return AIRateLimitError(
            "The Gemini free tier limit was hit. Wait a minute and try again, "
            "or check your quota in Google AI Studio."
        )
    if status == 404 or "not found" in text:
        return AIResponseError(
            "That Gemini model name was not found. Set GEMINI_MODEL in "
            "backend/.env to a model your account can use.",
        )
    if status in (500, 502, 503, 504):
        return AIOverloadedError("Gemini is temporarily unavailable. Try again shortly.")
    if "billing" in text:
        return AICreditExhaustedError("Google reports a billing problem on this project.")

    return AIResponseError("The Gemini request could not be completed.")


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 90) -> None:
        if not api_key.strip():
            raise AIUnavailableError("No Gemini API key configured.")
        self._api_key = api_key.strip()
        self._model = model
        self._timeout = float(timeout_seconds)

    def generate_json(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict[str, Any],
        schema_name: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": to_gemini_schema(json_schema),
                "maxOutputTokens": max_tokens,
                "temperature": 0.3,
            },
        }

        url = f"{BASE_URL}/{self._model}:generateContent"
        try:
            response = httpx.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self._api_key},
                timeout=self._timeout,
            )
        except httpx.RequestError as exc:
            logger.error("gemini_network_error", error=str(exc))
            raise AIOverloadedError(
                "Could not reach Gemini. Check your internet connection."
            ) from exc

        if response.status_code != 200:
            error = classify_gemini_error(response.status_code, response.text)
            logger.error(
                "gemini_call_failed",
                status=response.status_code,
                code=error.code,
                detail=response.text[:600],
            )
            raise error

        try:
            body = response.json()
            text = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            # A truncated or filtered response lands here.
            reason = ""
            try:
                reason = response.json()["candidates"][0].get("finishReason", "")
            except Exception:  # noqa: BLE001
                pass
            logger.error("gemini_no_content", finish_reason=reason)
            raise AIResponseError(
                "Gemini returned no usable content"
                + (f" (reason: {reason})." if reason else ".")
            ) from exc

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIResponseError("Gemini returned malformed JSON.") from exc
