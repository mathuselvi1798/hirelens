"""Output contract for the Job Match module."""
from typing import Literal

from pydantic import BaseModel, Field

Importance = Literal["critical", "important", "nice_to_have"]


class MatchedSkill(BaseModel):
    skill: str = Field(max_length=60, description="A requirement the candidate demonstrably meets")
    evidence: str = Field(
        max_length=220,
        description="Where in the resume this is shown. Quote or reference it; never invent.",
    )


class MissingSkill(BaseModel):
    skill: str = Field(max_length=60)
    importance: Importance = Field(description="How much this gap matters for this specific role")
    how_to_address: str = Field(
        max_length=260,
        description="A realistic way to close or offset this gap - a course, a project, or "
        "surfacing existing experience that already covers it.",
    )


class ExperienceAlignment(BaseModel):
    required: str = Field(max_length=80, description="What the posting asks for, e.g. '0-3 years'")
    candidate: str = Field(max_length=80, description="What the resume shows")
    aligned: bool
    comment: str = Field(max_length=300)


class KeywordCoverage(BaseModel):
    score: int = Field(ge=0, le=100, description="Share of important posting terms present in the resume")
    covered: list[str] = Field(max_length=20, description="Posting terms found in the resume")
    missing: list[str] = Field(
        max_length=20,
        description="Important posting terms absent from the resume, most damaging first",
    )


class JobMatch(BaseModel):
    match_score: int = Field(ge=0, le=100, description="Overall fit for this specific posting")
    verdict: Literal["strong_match", "good_match", "partial_match", "weak_match"]
    headline: str = Field(max_length=160, description="One sentence on where this candidate stands")
    summary: str = Field(max_length=900, description="2-4 honest sentences for the candidate")

    matching_skills: list[MatchedSkill] = Field(max_length=10)
    missing_skills: list[MissingSkill] = Field(max_length=10)
    experience_alignment: ExperienceAlignment
    keyword_coverage: KeywordCoverage

    recommendations: list[str] = Field(
        min_length=1,
        max_length=6,
        description="Specific changes to this resume that would improve the match for THIS role",
    )
    should_apply: Literal["yes", "yes_with_changes", "probably_not"] = Field(
        description="An honest call. 'probably_not' is a legitimate answer."
    )
    confidence: Literal["high", "medium", "low"]
