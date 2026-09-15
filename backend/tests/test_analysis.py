"""Tests for the analysis spine, using a fake AI provider.

The point of the provider interface is that the whole engine can be exercised
without a network call, an API key, or a cent of spend.
"""
import io
from typing import Any

import pytest

from app.ai.cache import InMemoryResultCache
from app.ai.client import AIClient
from app.analysis.base import AnalysisContext
from app.analysis.registry import all_modules, get_module
from app.analysis.service import run_analysis
from app.core.exceptions import AIResponseError, ModuleNotFoundError_
from app.documents.service import build_document
from tests.conftest import RESUME_TEXT

VALID_ANALYSIS: dict[str, Any] = {
    "overall_score": 78,
    "headline": "A solid backend resume held back by inconsistent impact framing.",
    "summary": "Clear structure and strong technical signal. Several bullets state duties rather than outcomes.",
    "clarity_score": 80,
    "impact_score": 68,
    "structure_score": 85,
    "estimated_experience_level": "senior",
    "sections": [
        {"name": "Experience", "present": True, "score": 80, "comment": "Well organized."}
    ],
    "skills": [{"category": "Languages", "skills": ["Python"]}],
    "strengths": [{"title": "Quantified impact", "detail": "Latency reduction is specific."}],
    "weaknesses": [
        {"title": "Duty-based bullets", "detail": "Some bullets describe responsibilities.", "severity": "medium"}
    ],
    "recommendations": [
        {
            "priority": "high",
            "area": "Impact",
            "action": "Rewrite duty-based bullets as outcomes.",
            "rationale": "Outcomes demonstrate capability; duties do not.",
            "example": None,
        }
    ],
    "confidence": "high",
}


class FakeProvider:
    """Returns whatever it is told to, and counts calls."""

    name = "fake"

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = responses
        self.calls = 0

    def generate_json(self, **_: Any) -> dict[str, Any]:
        response = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return response


@pytest.fixture
def context():
    return AnalysisContext(document=build_document("resume.txt", RESUME_TEXT.encode()))


def _client(settings, responses):
    provider = FakeProvider(responses)
    return AIClient(provider, settings, InMemoryResultCache()), provider


def test_registry_contains_resume_analysis():
    ids = [m.id for m in all_modules()]
    assert "resume_analysis" in ids


def test_unknown_module_raises():
    with pytest.raises(ModuleNotFoundError_):
        get_module("not_a_real_module")


def test_run_returns_validated_result(settings, context):
    ai, provider = _client(settings, [VALID_ANALYSIS])
    result = run_analysis(module_id="resume_analysis", ctx=context, ai=ai)

    assert result.module_id == "resume_analysis"
    assert result.data["overall_score"] == 78
    assert result.cached is False
    assert provider.calls == 1


def test_identical_input_is_served_from_cache(settings, context):
    ai, provider = _client(settings, [VALID_ANALYSIS])
    run_analysis(module_id="resume_analysis", ctx=context, ai=ai)
    second = run_analysis(module_id="resume_analysis", ctx=context, ai=ai)

    assert second.cached is True
    assert provider.calls == 1, "a cache hit must not call the model again"


def test_invalid_ai_output_is_retried_then_accepted(settings, context):
    broken = {**VALID_ANALYSIS, "overall_score": 140}  # violates le=100
    ai, provider = _client(settings, [broken, VALID_ANALYSIS])

    result = run_analysis(module_id="resume_analysis", ctx=context, ai=ai)

    assert provider.calls == 2, "the first, invalid response must trigger a retry"
    assert result.data["overall_score"] == 78


def test_persistently_invalid_output_raises(settings, context):
    broken = {**VALID_ANALYSIS, "confidence": "extremely-high"}
    ai, _ = _client(settings, [broken])

    with pytest.raises(AIResponseError):
        run_analysis(module_id="resume_analysis", ctx=context, ai=ai)


def test_modules_endpoint_lists_registered_modules(client):
    response = client.get("/api/v1/analysis/modules")
    assert response.status_code == 200
    assert any(m["id"] == "resume_analysis" for m in response.json())


def test_run_without_api_key_returns_503(client, resume_bytes):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("resume.txt", io.BytesIO(resume_bytes), "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.post(
        "/api/v1/analysis/resume_analysis/run", json={"document_id": document_id}
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_unavailable"
