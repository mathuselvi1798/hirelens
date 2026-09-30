"""Contract tests that every analysis module must pass.

These are written against the *registry*, not against a list of module names.
A new module is covered the moment it registers itself - which is the point of
the registry, and the only way a suite keeps up with a plug-in architecture.
"""
import io
import json

import pytest

from app.ai.cache import InMemoryResultCache
from app.ai.client import AIClient, _tool_schema, get_ai_client
from app.ai.schema_compat import ALLOWED, REJECTED_IN_PRACTICE, to_gemini_schema
from app.analysis.base import AnalysisContext
from app.analysis.registry import all_modules, get_module
from app.analysis.service import run_analysis
from app.core.config import get_settings
from app.core.exceptions import AIResponseError, ModuleInputError
from app.documents.service import build_document
from tests.conftest import RESUME_TEXT

EXPECTED_MODULES = {
    "resume_analysis",
    "job_match",
    "ats_analysis",
    "career_intelligence",
}

# A valid payload per module, used to drive the pipeline without a real model.
PAYLOADS: dict[str, dict] = {
    "resume_analysis": {
        "overall_score": 78, "headline": "h", "summary": "s",
        "clarity_score": 80, "impact_score": 68, "structure_score": 85,
        "estimated_experience_level": "senior",
        "sections": [{"name": "Experience", "present": True, "score": 80, "comment": "c"}],
        "skills": [{"category": "Languages", "skills": ["Python"]}],
        "strengths": [{"title": "t", "detail": "d"}],
        "weaknesses": [{"title": "t", "detail": "d", "severity": "medium"}],
        "recommendations": [
            {"priority": "high", "area": "Impact", "action": "a",
             "rationale": "r", "example": None}
        ],
        "confidence": "high",
    },
    "job_match": {
        "match_score": 72, "verdict": "good_match", "headline": "h", "summary": "s",
        "matching_skills": [{"skill": "Python", "evidence": "Built APIs"}],
        "missing_skills": [
            {"skill": "Kubernetes", "importance": "important", "how_to_address": "a"}
        ],
        "experience_alignment": {
            "required": "0-3 years", "candidate": "5 years",
            "aligned": True, "comment": "c",
        },
        "keyword_coverage": {"score": 66, "covered": ["python"], "missing": ["k8s"]},
        "recommendations": ["Add a metrics line"],
        "should_apply": "yes_with_changes", "confidence": "high",
    },
    "ats_analysis": {
        "ats_score": 80, "parse_risk": "low", "headline": "h", "summary": "s",
        "formatting": {"score": 85, "comment": "c"},
        "sections": {"score": 80, "comment": "c"},
        "keywords": {"score": 70, "comment": "c"},
        "readability": {"score": 75, "comment": "c"},
        "missing_sections": ["summary"], "suggested_keywords": ["SLA"],
        "issues": [{"severity": "medium", "area": "Dates", "issue": "i", "fix": "f"}],
        "confidence": "high",
    },
    "career_intelligence": {
        "headline": "h", "current_positioning": "p", "readiness_score": 68,
        "recommended_roles": [
            {"title": "Senior Engineer", "fit_score": 75, "why": "w", "gap_to_close": "g"}
        ],
        "skill_gaps": [{"skill": "K8s", "priority": "high", "why_it_matters": "w"}],
        "learning_roadmap": [
            {"step": 1, "focus": "f", "outcome": "o", "estimated_weeks": 4}
        ],
        "next_actions": [{"action": "a", "timeframe": "this_week"}],
        "confidence": "medium",
    },
}

MODULE_IDS = sorted(EXPECTED_MODULES)


class FakeProvider:
    """Returns a fixed payload and counts calls."""

    name = "fake"

    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls = 0

    def generate_json(self, **_):
        self.calls += 1
        return self.payload


@pytest.fixture
def document():
    return build_document("resume.txt", RESUME_TEXT.encode())


def _client(settings, payload):
    provider = FakeProvider(payload)
    return AIClient(provider, settings, InMemoryResultCache()), provider


# --- registry -------------------------------------------------------------

def test_expected_modules_are_registered():
    assert {m.id for m in all_modules()} == EXPECTED_MODULES


def test_every_module_declares_its_contract():
    for module in all_modules():
        assert module.id and module.title and module.description
        assert module.output_model is not None
        assert module.prompt_version


def test_modules_endpoint_lists_all_of_them(client):
    response = client.get("/api/v1/analysis/modules")
    assert response.status_code == 200
    assert {m["id"] for m in response.json()} == EXPECTED_MODULES


# --- vendor schema compatibility -----------------------------------------

@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_schema_survives_gemini_translation(module_id):
    """Guards the bug that cost us an afternoon: Gemini rejects keywords its
    own documentation lists as supported. If a future module reintroduces one,
    this fails here rather than as a blank 400 in front of a user."""
    schema = to_gemini_schema(_tool_schema(get_module(module_id).output_model))
    text = json.dumps(schema)

    for keyword in REJECTED_IN_PRACTICE:
        assert f'"{keyword}"' not in text, f"{keyword} would be rejected by Gemini"
    for keyword in ("anyOf", "$ref", "$defs", "additionalProperties"):
        assert keyword not in text, f"{keyword} survived translation"

    def walk(node, bad):
        if isinstance(node, dict):
            for key, value in node.items():
                if key not in ALLOWED:
                    bad.append(key)
                if key == "properties":
                    for field in value.values():
                        walk(field, bad)
                elif key == "items":
                    walk(value, bad)
        return bad

    assert not walk(schema, []), "schema contains keywords Gemini does not accept"


# --- behaviour ------------------------------------------------------------

@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_module_validates_and_caches(module_id, settings, document):
    ai, provider = _client(settings, PAYLOADS[module_id])
    ctx = AnalysisContext(document=document, job_description="Python role, Kubernetes")

    first = run_analysis(module_id=module_id, ctx=ctx, ai=ai)
    second = run_analysis(module_id=module_id, ctx=ctx, ai=ai)

    assert first.module_id == module_id
    assert first.cached is False
    assert second.cached is True
    assert provider.calls == 1, "a cache hit must not call the model again"


@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_prompt_builds_and_includes_the_resume(module_id, document):
    module = get_module(module_id)
    ctx = AnalysisContext(document=document, job_description="Python role")
    system, user = module.build_prompt(ctx)

    assert len(system) > 100
    assert "Karthik" in user, "the resume text must reach the prompt"


def test_job_match_refuses_without_a_job_description(settings, document):
    ai, provider = _client(settings, PAYLOADS["job_match"])

    with pytest.raises(ModuleInputError):
        run_analysis(
            module_id="job_match",
            ctx=AnalysisContext(document=document),
            ai=ai,
        )
    assert provider.calls == 0, "must fail before spending a model call"


def test_job_match_refuses_a_blank_job_description(settings, document):
    """A job description that is present but empty or whitespace-only is a
    different code path than None reaching the route (a frontend can easily
    send "" or "   " instead of omitting the field). This guards the .strip()
    call in run_analysis - swap it for an `is None` check and this fails."""
    ai, provider = _client(settings, PAYLOADS["job_match"])

    for blank in ("", "   ", "\n\t"):
        with pytest.raises(ModuleInputError):
            run_analysis(
                module_id="job_match",
                ctx=AnalysisContext(document=document, job_description=blank),
                ai=ai,
            )
    assert provider.calls == 0, "must fail before spending a model call"


def test_modules_not_needing_a_job_description_run_without_one(settings, document):
    for module_id in ("resume_analysis", "ats_analysis", "career_intelligence"):
        ai, _ = _client(settings, PAYLOADS[module_id])
        result = run_analysis(
            module_id=module_id, ctx=AnalysisContext(document=document), ai=ai
        )
        assert result.module_id == module_id


@pytest.mark.parametrize("module_id", ["ats_analysis", "career_intelligence"])
def test_optional_job_description_appears_in_prompt_only_when_given(module_id, document):
    """ats_analysis and career_intelligence both accept a job description but
    don't require one, and both add an extra prompt section only when it's
    present. Nothing previously checked that branch either fires or stays
    silent - a module can regress into always including it (leaking stale
    context into every analysis) or never including it (silently ignoring
    what the user typed) without any test noticing."""
    module = get_module(module_id)

    _, with_jd = module.build_prompt(
        AnalysisContext(document=document, job_description="Kubernetes SRE role")
    )
    _, without_jd = module.build_prompt(
        AnalysisContext(document=document, job_description=None)
    )

    assert "Kubernetes SRE role" in with_jd
    assert "Kubernetes SRE role" not in without_jd


@pytest.mark.parametrize(
    "module_id,field,bad_value",
    [
        ("resume_analysis", "overall_score", 140),
        ("job_match", "match_score", -5),
        ("ats_analysis", "parse_risk", "catastrophic"),
        ("career_intelligence", "readiness_score", 999),
    ],
)
def test_invalid_ai_output_is_rejected(module_id, field, bad_value, settings, document):
    broken = {**PAYLOADS[module_id], field: bad_value}
    ai, _ = _client(settings, broken)
    ctx = AnalysisContext(document=document, job_description="Python role")

    with pytest.raises(AIResponseError):
        run_analysis(module_id=module_id, ctx=ctx, ai=ai)


@pytest.mark.parametrize(
    "module_id,field,extra_count",
    [
        ("job_match", "matching_skills", 10),  # max_length=10, base has 1 -> 11
        ("ats_analysis", "issues", 10),  # max_length=10, base has 1 -> 11
        ("career_intelligence", "skill_gaps", 8),  # max_length=8, base has 1 -> 9
    ],
)
def test_list_max_length_is_enforced(module_id, field, extra_count, settings, document):
    """The schemas cap list lengths (so a rambling model can't blow up the
    UI), but nothing previously drove an AI response over those caps. A
    provider that ignores the limit and returns 30 "missing skills" should
    fail validation here, not render as a wall of text in the frontend."""
    one_item = PAYLOADS[module_id][field][0]
    broken = {**PAYLOADS[module_id], field: [one_item] * (extra_count + 1)}
    ai, _ = _client(settings, broken)
    ctx = AnalysisContext(document=document, job_description="Python role")

    with pytest.raises(AIResponseError):
        run_analysis(module_id=module_id, ctx=ctx, ai=ai)


def test_job_description_is_part_of_the_cache_key(settings, document):
    """Two different postings must not share one cached match result."""
    ai, provider = _client(settings, PAYLOADS["job_match"])

    run_analysis(
        module_id="job_match",
        ctx=AnalysisContext(document=document, job_description="Python role"),
        ai=ai,
    )
    run_analysis(
        module_id="job_match",
        ctx=AnalysisContext(document=document, job_description="Java role"),
        ai=ai,
    )
    assert provider.calls == 2


# --- HTTP layer -------------------------------------------------------------
# Everything above drives run_analysis() directly. These go through the real
# route (client.post), which is what a browser actually calls - resume_analysis
# had this coverage (test_analysis.py), the other three modules didn't.

@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_run_endpoint_succeeds_for_every_module(module_id, client, resume_bytes):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("resume.txt", io.BytesIO(resume_bytes), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    provider = FakeProvider(PAYLOADS[module_id])
    test_settings = client.app.dependency_overrides[get_settings]()
    fake_ai = AIClient(provider, test_settings, InMemoryResultCache())
    client.app.dependency_overrides[get_ai_client] = lambda: fake_ai

    response = client.post(
        f"/api/v1/analysis/{module_id}/run",
        json={"document_id": document_id, "job_description": "Python role, Kubernetes"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module_id"] == module_id
    assert body["cached"] is False
    assert provider.calls == 1


def test_run_endpoint_rejects_job_match_without_a_job_description(client, resume_bytes):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("resume.txt", io.BytesIO(resume_bytes), "text/plain")},
    )
    document_id = upload.json()["id"]

    test_settings = client.app.dependency_overrides[get_settings]()
    fake_ai = AIClient(FakeProvider(PAYLOADS["job_match"]), test_settings, InMemoryResultCache())
    client.app.dependency_overrides[get_ai_client] = lambda: fake_ai

    response = client.post(
        "/api/v1/analysis/job_match/run",
        json={"document_id": document_id},
    )

    assert response.status_code == 400
    assert "job description" in response.json()["error"]["message"].lower()


def test_run_endpoint_404s_for_an_unknown_document(client):
    test_settings = client.app.dependency_overrides[get_settings]()
    fake_ai = AIClient(
        FakeProvider(PAYLOADS["resume_analysis"]), test_settings, InMemoryResultCache()
    )
    client.app.dependency_overrides[get_ai_client] = lambda: fake_ai

    response = client.post(
        "/api/v1/analysis/resume_analysis/run",
        json={"document_id": "does-not-exist"},
    )

    assert response.status_code == 404
