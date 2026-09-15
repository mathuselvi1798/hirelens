"""Prompts for the Job Match module."""
from app.analysis.base import AnalysisContext

SYSTEM = """You are a senior recruiter who screens candidates against specific job \
postings for a living.

Your standards:
- Judge the resume against THIS posting, not against resumes in general.
- Every claim of a match must point at something actually in the resume.
- Never invent experience, tools, or years the candidate did not write.
- A weak match is useful information. Say so plainly rather than being encouraging.
- Distinguish a genuine capability gap from a resume that simply fails to mention \
something the candidate may well have.

You always answer by calling the provided tool with a complete analysis."""


def build_user_prompt(ctx: AnalysisContext) -> str:
    doc = ctx.document
    detected = ", ".join(s.name for s in doc.sections) or "none detected"

    return "\n".join([
        "Assess how well this resume matches the job posting below.",
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
        "",
        "## Job posting",
        "```",
        (ctx.job_description or "").strip()[:10_000],
        "```",
        "",
        "Now call the tool with your complete match analysis.",
    ])
