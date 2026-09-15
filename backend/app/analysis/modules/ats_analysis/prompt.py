"""Prompts for the ATS Analysis module."""
from app.analysis.base import AnalysisContext

SYSTEM = """You are an expert on applicant tracking systems and resume parsing.

Your standards:
- You are judging machine readability first, human readability second.
- The strongest evidence you have is the extracted text itself: if it arrived \
garbled, out of order, or missing obvious sections, that is exactly what an ATS \
will see too.
- Never suggest keyword stuffing. Suggest a term only if the candidate plausibly \
has the experience already.
- Be concrete. "Improve formatting" is useless; "the two-column layout interleaved \
your job titles with dates" is useful.

You always answer by calling the provided tool with a complete analysis."""


def build_user_prompt(ctx: AnalysisContext) -> str:
    doc = ctx.document
    detected = ", ".join(s.name for s in doc.sections) or "none detected"

    contact = []
    if doc.contact.email:
        contact.append("email found")
    if doc.contact.phone:
        contact.append("phone found")
    if doc.contact.links:
        contact.append(f"{len(doc.contact.links)} link(s)")

    parts = [
        "Assess how well this resume will survive automated parsing.",
        "",
        "## Parser metadata (this is literally what a parser extracted)",
        f"- File type: {doc.file_type}",
        f"- Pages: {doc.page_count if doc.page_count is not None else 'unknown'}",
        f"- Word count: {doc.word_count}",
        f"- Sections detected: {detected}",
        f"- Bullet points detected: {len(doc.bullets)}",
        f"- Contact info: {', '.join(contact) or 'none detected'}",
        "",
        "Treat this as strong evidence. A section the parser missed is a section an "
        "ATS will likely miss. Zero detected bullets in a resume full of bullet "
        "characters means the layout is interfering.",
        "",
        "## Extracted text, exactly as the parser produced it",
        "```",
        doc.raw_text[:20_000],
        "```",
    ]

    if ctx.job_description and ctx.job_description.strip():
        parts += [
            "",
            "## Target posting (for keyword relevance only)",
            "```",
            ctx.job_description.strip()[:6_000],
            "```",
        ]

    parts += ["", "Now call the tool with your complete ATS analysis."]
    return "\n".join(parts)
