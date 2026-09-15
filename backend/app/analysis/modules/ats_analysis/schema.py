"""Output contract for the ATS Analysis module."""
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["high", "medium", "low"]


class ATSIssue(BaseModel):
    severity: Severity
    area: str = Field(max_length=50, description="e.g. 'Formatting', 'Sections', 'Dates'")
    issue: str = Field(max_length=260, description="What an automated parser is likely to get wrong")
    fix: str = Field(max_length=260, description="The concrete change that removes the risk")


class ScoredArea(BaseModel):
    score: int = Field(ge=0, le=100)
    comment: str = Field(max_length=400)


class ATSAnalysis(BaseModel):
    ats_score: int = Field(ge=0, le=100, description="How reliably an ATS will parse this resume")
    parse_risk: Literal["low", "medium", "high"] = Field(
        description="Risk that an automated system mangles or drops content"
    )
    headline: str = Field(max_length=160)
    summary: str = Field(max_length=800, description="2-4 sentences in plain language")

    formatting: ScoredArea = Field(
        description="Columns, tables, graphics, headers/footers, fonts, symbols - anything that "
        "confuses a parser. Judge from how cleanly the text extracted."
    )
    sections: ScoredArea = Field(
        description="Whether standard, conventionally-named sections are present and detectable"
    )
    keywords: ScoredArea = Field(
        description="Whether role-relevant terms appear in plain text where a parser will index them"
    )
    readability: ScoredArea = Field(
        description="Sentence and bullet length, jargon density, scannability by a human in 10 seconds"
    )

    missing_sections: list[str] = Field(
        max_length=8, description="Standard sections a recruiter expects but could not be found"
    )
    suggested_keywords: list[str] = Field(
        max_length=15,
        description="Terms worth adding IF the candidate genuinely has them. Never fabricate.",
    )
    issues: list[ATSIssue] = Field(max_length=10)
    confidence: Literal["high", "medium", "low"]
