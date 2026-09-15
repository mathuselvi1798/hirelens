"""Prompts for the Career Intelligence module."""
from app.analysis.base import AnalysisContext

SYSTEM = """You are a career strategist who advises people on their realistic next \
move, not their dream job.

Your standards:
- Recommend roles this person could plausibly reach within 6-12 months, given what \
the resume actually shows.
- Ground every recommendation in evidence from the resume.
- A roadmap is only useful if it is sequenced and finite. Six vague suggestions help \
nobody; three concrete steps with an outcome each do.
- Do not inflate. If the profile is early-career or thin, say so kindly and aim the \
advice accordingly.
- Never invent experience, and never promise outcomes.

You always answer by calling the provided tool with a complete analysis."""


def build_user_prompt(ctx: AnalysisContext) -> str:
    doc = ctx.document
    detected = ", ".join(s.name for s in doc.sections) or "none detected"

    parts = [
        "Give this candidate a realistic read on their career options and a plan.",
        "",
        "## Parser metadata",
        f"- Word count: {doc.word_count}",
        f"- Sections detected: {detected}",
        f"- Bullet points: {len(doc.bullets)}",
        "",
        "## Resume",
        "```",
        doc.raw_text[:20_000],
        "```",
    ]

    if ctx.job_description and ctx.job_description.strip():
        parts += [
            "",
            "## A role they are currently targeting",
            "Use this as a signal of direction. Say honestly whether it is the right "
            "target, and recommend alternatives if something fits better.",
            "```",
            ctx.job_description.strip()[:6_000],
            "```",
        ]

    parts += ["", "Now call the tool with your complete career analysis."]
    return "\n".join(parts)
