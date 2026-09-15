"""Output contract for the Career Intelligence module."""
from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["critical", "high", "medium", "low"]


class RoleRecommendation(BaseModel):
    title: str = Field(max_length=70, description="A realistic next role title")
    fit_score: int = Field(ge=0, le=100, description="How well the current profile fits this role today")
    why: str = Field(max_length=300, description="What in the resume supports this, specifically")
    gap_to_close: str = Field(
        max_length=220, description="The main thing standing between the candidate and this role"
    )


class SkillGap(BaseModel):
    skill: str = Field(max_length=60)
    priority: Priority
    why_it_matters: str = Field(max_length=260, description="What this unlocks for the roles above")


class LearningStep(BaseModel):
    step: int = Field(ge=1, le=8, description="Order in the roadmap, starting at 1")
    focus: str = Field(max_length=80, description="What to learn or build in this step")
    outcome: str = Field(max_length=220, description="What the candidate can show afterwards")
    estimated_weeks: int = Field(ge=1, le=52)


class NextAction(BaseModel):
    action: str = Field(max_length=220, description="Something doable this week or this month")
    timeframe: Literal["this_week", "this_month", "this_quarter"]


class CareerIntelligence(BaseModel):
    headline: str = Field(max_length=160, description="One sentence on where this career stands now")
    current_positioning: str = Field(
        max_length=700,
        description="An honest read of how the market would currently see this candidate",
    )
    readiness_score: int = Field(
        ge=0, le=100, description="How ready this profile is for the recommended roles today"
    )

    recommended_roles: list[RoleRecommendation] = Field(min_length=1, max_length=5)
    skill_gaps: list[SkillGap] = Field(max_length=8)
    learning_roadmap: list[LearningStep] = Field(
        min_length=1, max_length=6, description="Sequenced, realistic, and specific to this person"
    )
    next_actions: list[NextAction] = Field(min_length=1, max_length=6)
    confidence: Literal["high", "medium", "low"]
