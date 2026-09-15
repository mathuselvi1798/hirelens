"""Output contract for the Resume Analysis module.

This schema is doing three jobs at once:
  1. It is the tool schema the model must fill in, so field descriptions here
     are prompt engineering, not documentation.
  2. It is the validation gate - anything malformed is rejected before it can
     reach the UI.
  3. It is the source of the frontend's TypeScript types.

Constraints are intentionally tight. `ge=0, le=100` on a score means a model
that returns 105 triggers a retry instead of a broken progress bar.
"""
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["high", "medium", "low"]
Priority = Literal["critical", "high", "medium", "low"]


class SectionAssessment(BaseModel):
    name: str = Field(description="Section name, e.g. 'Experience', 'Skills'")
    present: bool = Field(description="Whether this section exists in the resume")
    score: int = Field(ge=0, le=100, description="Quality of this section, 0-100")
    comment: str = Field(
        max_length=400, description="One or two sentences on this section specifically"
    )


class Strength(BaseModel):
    title: str = Field(max_length=90, description="Short label for the strength")
    detail: str = Field(
        max_length=400,
        description="Why this is a strength, quoting or referencing the resume",
    )


class Weakness(BaseModel):
    title: str = Field(max_length=90)
    detail: str = Field(max_length=400, description="What is wrong and why it matters")
    severity: Severity


class Recommendation(BaseModel):
    priority: Priority
    area: str = Field(max_length=60, description="e.g. 'Impact', 'Formatting', 'Skills'")
    action: str = Field(
        max_length=300, description="A specific, concrete action the candidate can take"
    )
    rationale: str = Field(
        max_length=300, description="Why this action improves the resume"
    )
    example: str | None = Field(
        default=None,
        max_length=400,
        description=(
            "Optional rewritten line showing the improvement. Only rewrite wording "
            "the candidate already wrote; never invent facts or metrics."
        ),
    )


class SkillGroup(BaseModel):
    category: str = Field(max_length=60, description="e.g. 'Languages', 'Cloud', 'Soft skills'")
    skills: list[str] = Field(max_length=25)


class ResumeAnalysis(BaseModel):
    overall_score: int = Field(ge=0, le=100, description="Holistic resume quality, 0-100")
    headline: str = Field(
        max_length=160,
        description="One sentence summarizing the resume's current standing",
    )
    summary: str = Field(
        max_length=900, description="2-4 sentence honest assessment for the candidate"
    )

    clarity_score: int = Field(ge=0, le=100)
    impact_score: int = Field(ge=0, le=100, description="Use of quantified, outcome-focused achievements")
    structure_score: int = Field(ge=0, le=100)

    estimated_experience_level: Literal[
        "student", "entry", "junior", "mid", "senior", "lead", "executive", "unclear"
    ]

    sections: list[SectionAssessment] = Field(min_length=1, max_length=12)
    skills: list[SkillGroup] = Field(max_length=8)
    strengths: list[Strength] = Field(min_length=1, max_length=6)
    weaknesses: list[Weakness] = Field(max_length=6)
    recommendations: list[Recommendation] = Field(min_length=1, max_length=8)

    confidence: Literal["high", "medium", "low"] = Field(
        description=(
            "How confident this analysis is, given the quality and completeness of "
            "the extracted text. Use 'low' when the document was sparse or garbled."
        )
    )
